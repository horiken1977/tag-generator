import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 300 // 300秒（5分）に延長して大量キーワード処理に対応

interface VideoData {
  title?: string
  skill?: string
  description?: string
  summary?: string
  transcript?: string
}


function collectBatchTexts(processData: VideoData[]): string {
  const allTitles: string[] = []
  const allSkills: string[] = []
  const allDescriptions: string[] = []
  const allSummaries: string[] = []

  processData.forEach(video => {
    if (video.title) allTitles.push(video.title.slice(0, 200))
    if (video.skill) allSkills.push(video.skill.slice(0, 100))
    if (video.description) allDescriptions.push(video.description.slice(0, 300))
    if (video.summary) allSummaries.push(video.summary.slice(0, 400))
  })

  return [
    ...allTitles,
    ...allSkills,
    ...allDescriptions,
    ...allSummaries
  ].join(' ')
}

// Stage1A: 個別キーワード抽出（1行ずつ軽量処理）
async function extractKeywordsFromSingleRow(videoData: VideoData): Promise<string[]> {
  // 1行分のテキストを構築（文字起こし除外）
  const rowText = [
    videoData.title || '',
    videoData.skill || '',
    videoData.description || '',
    videoData.summary || ''
  ].filter(text => text.trim()).join(' ')

  console.log(`🔍 1行分析: "${rowText.slice(0, 50)}..." (${rowText.length}文字)`)

  // AI API環境変数チェック
  const hasOpenAI = !!process.env.OPENAI_API_KEY
  const hasClaude = !!process.env.CLAUDE_API_KEY
  const hasGemini = !!process.env.GEMINI_API_KEY
  
  if (!hasOpenAI && !hasClaude && !hasGemini) {
    throw new Error('AI APIキーが設定されていません。')
  }

  const startTime = Date.now()
  const aiClient = new AIClient()
  const aiEngine = hasOpenAI ? 'openai' : hasClaude ? 'claude' : 'gemini'
  
  // 軽量なキーワード抽出
  const keywords = await aiClient.extractKeywordsLight(rowText, aiEngine)
  
  const processingTime = Date.now() - startTime
  console.log(`✅ 1行分析完了: ${keywords.length}個のキーワード, 処理時間: ${processingTime}ms`)

  return keywords
}

// Stage1B: 全体最適化（収集したキーワードから200個のタグ生成）
async function optimizeGlobalTags(allKeywords: string[]): Promise<string[]> {
  console.log(`🌐 全体最適化開始: ${allKeywords.length}個のキーワードから200個のタグを生成`)

  // AI API環境変数チェック
  const hasOpenAI = !!process.env.OPENAI_API_KEY
  const hasClaude = !!process.env.CLAUDE_API_KEY
  const hasGemini = !!process.env.GEMINI_API_KEY
  
  if (!hasOpenAI && !hasClaude && !hasGemini) {
    throw new Error('AI APIキーが設定されていません。')
  }

  const aiClient = new AIClient()
  const aiEngine = hasOpenAI ? 'openai' : hasClaude ? 'claude' : 'gemini'
  
  // 大量キーワードの場合は多段階で処理
  if (allKeywords.length > 5000) {
    console.log(`📊 大量キーワード検出: ${allKeywords.length}個 → 多段階処理を開始`)
    
    // Step 1: 頻度分析で上位キーワードを抽出
    const frequencyMap = new Map<string, number>()
    allKeywords.forEach(keyword => {
      const normalized = keyword.toLowerCase().trim()
      frequencyMap.set(normalized, (frequencyMap.get(normalized) || 0) + 1)
    })
    
    // 頻度順にソートして上位を取得
    const sortedKeywords = Array.from(frequencyMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5000)
      .map(([keyword]) => keyword)
    
    console.log(`📈 Step 1: 頻度分析完了 → ${sortedKeywords.length}個の高頻度キーワード`)
    
    // Step 2: バッチ処理で段階的に削減
    const batchSize = 1000
    const batches = []
    for (let i = 0; i < sortedKeywords.length; i += batchSize) {
      batches.push(sortedKeywords.slice(i, i + batchSize))
    }
    
    console.log(`🔄 Step 2: ${batches.length}個のバッチに分割`)
    
    const intermediateResults: string[] = []
    for (let i = 0; i < batches.length; i++) {
      console.log(`   バッチ ${i + 1}/${batches.length} を処理中...`)
      const batchResults = await aiClient.optimizeTags(batches[i], aiEngine)
      intermediateResults.push(...batchResults.slice(0, 50)) // 各バッチから最大50個
    }
    
    console.log(`📊 Step 2完了: ${intermediateResults.length}個の中間タグ`)
    
    // Step 3: 最終的な200個への絞り込み
    console.log(`🎯 Step 3: 最終最適化 → 200個のタグへ`)
    const startTime = Date.now()
    const finalTags = await aiClient.optimizeTags(intermediateResults, aiEngine)
    const processingTime = Date.now() - startTime
    
    console.log(`✅ 多段階最適化完了: ${finalTags.length}個のタグ, 最終処理時間: ${processingTime}ms`)
    return finalTags
    
  } else {
    // 通常の処理
    const startTime = Date.now()
    const optimizedTags = await aiClient.optimizeTags(allKeywords, aiEngine)
    const processingTime = Date.now() - startTime
    console.log(`✅ 全体最適化完了: ${optimizedTags.length}個のタグ, 処理時間: ${processingTime}ms`)
    return optimizedTags
  }
}

export async function POST(request: NextRequest) {
  console.log('🚀 Stage1 ハイブリッド処理開始')
  try {
    const body = await request.json()
    const mode = body.mode // 'extract' または 'optimize'
    
    if (mode === 'extract') {
      // Stage1A: 個別キーワード抽出
      const videoData: VideoData = body.video_data
      const rowIndex = body.row_index
      
      console.log(`🔍 Stage1A: 行${rowIndex}のキーワード抽出開始`)
      
      if (!videoData) {
        return NextResponse.json({
          success: false,
          error: '動画データがありません'
        }, { status: 400 })
      }
      
      const startTime = Date.now()
      const keywords = await extractKeywordsFromSingleRow(videoData)
      const processingTime = Date.now() - startTime
      
      return NextResponse.json({
        stage: '1A',
        success: true,
        keywords: keywords,
        keyword_count: keywords.length,
        processing_time: processingTime / 1000,
        row_index: rowIndex,
        message: `行${rowIndex}から${keywords.length}個のキーワードを抽出しました`
      })
      
    } else if (mode === 'optimize') {
      // Stage1B: 全体最適化
      let allKeywords: string[] = body.all_keywords || []
      const totalRows = body.total_rows || 0
      
      console.log(`🌐 Stage1B: ${allKeywords.length}個のキーワードから200個のタグを最適化生成`)
      
      if (!allKeywords.length) {
        return NextResponse.json({
          success: false,
          error: 'キーワードデータがありません'
        }, { status: 400 })
      }
      
      // 基本的な重複削除（多段階処理で対応するため制限は撤廃）
      const originalCount = allKeywords.length
      allKeywords = [...new Set(allKeywords)]
      const dedupedCount = allKeywords.length
      
      if (originalCount !== dedupedCount) {
        console.log(`📊 重複削除: ${originalCount}個 → ${dedupedCount}個`)
      }
      
      const startTime = Date.now()
      const optimizedTags = await optimizeGlobalTags(allKeywords)
      const processingTime = Date.now() - startTime
      
      return NextResponse.json({
        stage: '1B',
        success: true,
        tag_candidates: optimizedTags,
        candidate_count: optimizedTags.length,
        processing_time: processingTime / 1000,
        source_data_stats: {
          total_videos: totalRows,
          total_keywords_processed: allKeywords.length,
          transcripts_excluded: true
        },
        message: `${allKeywords.length}個のキーワードから${optimizedTags.length}個の最適タグを生成しました（処理時間: ${(processingTime/1000).toFixed(1)}秒）`
      })
      
    } else {
      return NextResponse.json({
        success: false,
        error: 'mode パラメータが必要です。"extract" または "optimize" を指定してください。',
        stage: 1
      }, { status: 400 })
    }

  } catch (error: any) {
    console.error('❌ Stage1 API error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name,
      cause: error.cause
    })
    return NextResponse.json({
      success: false,
      error: `第1段階処理エラー: ${error.message}`,
      error_details: {
        name: error.name,
        message: error.message,
        stack: error.stack?.substring(0, 500)
      },
      stage: 1
    }, { status: 500 })
  }
}