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
  const functionStartTime = Date.now()
  const functionId = Math.random().toString(36).substr(2, 6)
  console.log(`🌐 [${functionId}] 全体最適化開始: ${allKeywords.length}個のキーワードから200個のタグを生成`)

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
    console.log(`📊 [${functionId}] 大量キーワード検出: ${allKeywords.length}個 → 超効率多段階処理を開始`)
    
    // Step 1: 効率的な頻度分析とメモリ最適化
    const frequencyMap = new Map<string, number>()
    
    // メモリ効率化: 5文字未満やstop wordは除外
    const stopWords = new Set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall'])
    
    allKeywords.forEach(keyword => {
      const normalized = keyword.toLowerCase().trim()
      // フィルタリング: 3文字以上、数字のみ除外、stop word除外
      if (normalized.length >= 3 && !stopWords.has(normalized) && !/^\d+$/.test(normalized)) {
        frequencyMap.set(normalized, (frequencyMap.get(normalized) || 0) + 1)
      }
    })
    
    console.log(`📈 Step 1: フィルタリング完了 → ${frequencyMap.size}個の有効キーワード (元: ${allKeywords.length}個)`)
    
    // 頻度上位2000個のみ処理対象にして負荷軽減
    const sortedKeywords = Array.from(frequencyMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2000)
      .map(([keyword]) => keyword)
    
    console.log(`📈 Step 1完了: 頻度上位${sortedKeywords.length}個を選択`)
    
    // Step 2: 小さなバッチで段階的処理（メモリ負荷軽減）
    const batchSize = 400  // さらに小さなバッチサイズ
    const batches = []
    for (let i = 0; i < sortedKeywords.length; i += batchSize) {
      batches.push(sortedKeywords.slice(i, i + batchSize))
    }
    
    console.log(`🔄 [${functionId}] Step 2: ${batches.length}個の小バッチに分割`)
    
    const intermediateResults: string[] = []
    for (let i = 0; i < batches.length; i++) {
      try {
        const batchStartTime = Date.now()
        console.log(`   [${functionId}] バッチ ${i + 1}/${batches.length} 開始... (${batches[i].length}個) - ${new Date().toISOString()}`)
        
        const batchResults = await aiClient.optimizeTags(batches[i], aiEngine)
        const batchTime = Date.now() - batchStartTime
        
        intermediateResults.push(...batchResults.slice(0, 30)) // 各バッチから最大30個に制限
        console.log(`   ✅ [${functionId}] バッチ ${i + 1} 完了: ${batchResults.length}個→${Math.min(batchResults.length, 30)}個選択, ${batchTime}ms`)
        
        // バッチ間に短い待機時間を追加（API制限対策）
        if (i < batches.length - 1) {
          console.log(`   ⏳ [${functionId}] バッチ間待機: 500ms`)
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      } catch (batchError: any) {
        console.error(`❌ [${functionId}] バッチ ${i + 1} エラー:`, batchError.message)
        // バッチエラーでも処理を継続
        continue
      }
    }
    
    console.log(`📊 Step 2完了: ${intermediateResults.length}個の中間タグ`)
    
    // Step 3: 最終的な200個への絞り込み
    if (intermediateResults.length === 0) {
      throw new Error('中間処理でタグが生成されませんでした。AI APIの調整が必要です。')
    }
    
    console.log(`🎯 Step 3: 最終最適化 → 200個のタグへ (入力: ${intermediateResults.length}個)`)
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
  const requestStartTime = Date.now()
  const requestId = Math.random().toString(36).substr(2, 9)
  console.log(`🚀 [${requestId}] Stage1 ハイブリッド処理開始 - ${new Date().toISOString()}`)
  
  try {
    const bodyParseStart = Date.now()
    const body = await request.json()
    const bodyParseTime = Date.now() - bodyParseStart
    console.log(`📄 [${requestId}] リクエストボディ解析完了: ${bodyParseTime}ms`)
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
      
      console.log(`🌐 [${requestId}] Stage1B開始: ${allKeywords.length}個のキーワードから200個のタグを最適化生成`)
      console.log(`📊 [${requestId}] 入力データ詳細: 総行数=${totalRows}, キーワード数=${allKeywords.length}, 最初の5キーワード=[${allKeywords.slice(0, 5).join(', ')}]`)
      
      if (!allKeywords.length) {
        return NextResponse.json({
          success: false,
          error: 'キーワードデータがありません'
        }, { status: 400 })
      }
      
      // 基本的な重複削除と事前フィルタリング（メモリ効率化）
      const originalCount = allKeywords.length
      const preprocessStart = Date.now()
      console.log(`🔍 [${requestId}] 事前処理開始: ${originalCount}個のキーワード`)
      
      // メモリ効率的な重複削除とフィルタリング
      const uniqueKeywords = new Set<string>()
      let processedCount = 0
      allKeywords.forEach(keyword => {
        processedCount++
        if (processedCount % 10000 === 0) {
          console.log(`   [${requestId}] 事前処理進捗: ${processedCount}/${originalCount} (${((processedCount/originalCount)*100).toFixed(1)}%)`)
        }
        const normalized = keyword?.toLowerCase()?.trim()
        if (normalized && normalized.length >= 2) {
          uniqueKeywords.add(normalized)
        }
      })
      
      allKeywords = Array.from(uniqueKeywords)
      const dedupedCount = allKeywords.length
      const preprocessTime = Date.now() - preprocessStart
      
      console.log(`📊 [${requestId}] 事前処理完了: ${originalCount}個 → ${dedupedCount}個 (重複削除 + フィルタリング) - ${preprocessTime}ms`)
      
      // 巨大データセットの場合はさらなる事前削減
      if (allKeywords.length > 80000) {
        console.log(`⚠️  [${requestId}] 超大量データセット検出: ${allKeywords.length}個 → 事前削減を実施`)
        allKeywords = allKeywords.slice(0, 80000)
        console.log(`📉 [${requestId}] 事前削減完了: ${allKeywords.length}個に制限`)
      }
      
      const startTime = Date.now()
      let optimizedTags: string[] = []
      
      try {
        console.log(`🎯 [${requestId}] optimizeGlobalTags呼び出し開始: ${allKeywords.length}個`)
        const optimizeStart = Date.now()
        optimizedTags = await optimizeGlobalTags(allKeywords)
        const optimizeTime = Date.now() - optimizeStart
        console.log(`✅ [${requestId}] optimizeGlobalTags完了: ${optimizeTime}ms`)
      } catch (optimizeError: any) {
        console.error(`❌ [${requestId}] 最適化エラー: ${optimizeError.message}`)
        
        // フォールバック: 頻度ベースの簡易タグ生成
        console.log(`🔄 フォールバック処理: 頻度ベースタグ生成`)
        const frequencyMap = new Map<string, number>()
        allKeywords.forEach(keyword => {
          const normalized = keyword.toLowerCase().trim()
          if (normalized.length >= 3) {
            frequencyMap.set(normalized, (frequencyMap.get(normalized) || 0) + 1)
          }
        })
        
        optimizedTags = Array.from(frequencyMap.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 200)
          .map(([keyword]) => keyword)
        
        console.log(`✅ フォールバック完了: ${optimizedTags.length}個のタグ生成`)
      }
      
      const processingTime = Date.now() - startTime
      const totalRequestTime = Date.now() - requestStartTime
      
      console.log(`🏁 [${requestId}] Stage1B完了: 処理時間=${processingTime}ms, 総リクエスト時間=${totalRequestTime}ms, タグ数=${optimizedTags.length}`)
      
      return NextResponse.json({
        stage: '1B',
        success: true,
        tag_candidates: optimizedTags,
        candidate_count: optimizedTags.length,
        processing_time: processingTime / 1000,
        source_data_stats: {
          total_videos: totalRows,
          total_keywords_processed: allKeywords.length,
          transcripts_excluded: true,
          fallback_used: optimizedTags.length > 0 && allKeywords.length > 50000
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