import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 60 // 60秒に延長してLLM処理時間を確保

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

  const startTime = Date.now()
  const aiClient = new AIClient()
  const aiEngine = hasOpenAI ? 'openai' : hasClaude ? 'claude' : 'gemini'
  
  // キーワードを統合して最適なタグ生成
  const optimizedTags = await aiClient.optimizeTags(allKeywords, aiEngine)
  
  const processingTime = Date.now() - startTime
  console.log(`✅ 全体最適化完了: ${optimizedTags.length}個のタグ, 処理時間: ${processingTime}ms`)

  return optimizedTags
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
      
      // キーワード数が多すぎる場合は重複を削除して制限
      if (allKeywords.length > 10000) {
        console.log(`⚠️ キーワード数が多すぎます (${allKeywords.length}個)。重複削除と制限を適用します。`)
        // 重複を削除
        const uniqueKeywords = [...new Set(allKeywords)]
        console.log(`📊 重複削除後: ${uniqueKeywords.length}個`)
        
        // それでも多い場合は、ランダムサンプリング
        if (uniqueKeywords.length > 10000) {
          // シャッフルして最初の10000個を取得
          const shuffled = uniqueKeywords.sort(() => 0.5 - Math.random())
          allKeywords = shuffled.slice(0, 10000)
          console.log(`🎲 ランダムサンプリング後: ${allKeywords.length}個`)
        } else {
          allKeywords = uniqueKeywords
        }
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