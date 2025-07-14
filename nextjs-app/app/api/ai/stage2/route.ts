import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 300 // Stage2は各行をLLM分析するため5分に延長

interface VideoData {
  title: string
  skill: string
  description: string
  summary: string
  transcript: string
}

// LLMを使用した動画タグ選択（文字起こし含む5列分析）
async function selectTagsForVideoWithAI(video: VideoData, approvedCandidates: string[], aiEngine: string): Promise<{ tags: string[], processingTime: number }> {
  const startTime = Date.now()
  
  // 動画の全データを構築（5列すべて含む）
  const videoContent = [
    `タイトル: ${video.title}`,
    `スキル: ${video.skill}`,
    `説明: ${video.description}`,
    `要約: ${video.summary}`,
    `文字起こし: ${video.transcript}`
  ].join('\n\n')

  console.log(`🎥 LLM分析開始: "${video.title.slice(0, 50)}..." - エンジン: ${aiEngine}`)
  
  // AI API環境変数チェック
  const hasOpenAI = !!process.env.OPENAI_API_KEY
  const hasClaude = !!process.env.CLAUDE_API_KEY
  const hasGemini = !!process.env.GEMINI_API_KEY
  
  // エンジン選択とフォールバック設定
  let engines: string[] = []
  if ((aiEngine === 'openai' && hasOpenAI) || 
      (aiEngine === 'claude' && hasClaude) || 
      (aiEngine === 'gemini' && hasGemini)) {
    engines.push(aiEngine)
    // フォールバック用
    if (aiEngine !== 'claude' && hasClaude) engines.push('claude')
    if (aiEngine !== 'gemini' && hasGemini) engines.push('gemini') 
    if (aiEngine !== 'openai' && hasOpenAI) engines.push('openai')
  } else {
    engines = [
      ...(hasClaude ? ['claude'] : []),
      ...(hasGemini ? ['gemini'] : []),
      ...(hasOpenAI ? ['openai'] : [])
    ]
  }

  const aiClient = new AIClient()
  let selectedTags: string[] = []
  let lastError: any = null

  // フォールバック機能付きでAI呼び出し
  for (const engine of engines) {
    try {
      console.log(`🔄 ${engine}でタグ選択を試行中...${engine === aiEngine ? ' (ユーザー選択)' : ' (フォールバック)'}`)
      selectedTags = await aiClient.selectTagsForVideo(videoContent, approvedCandidates, engine)
      console.log(`✅ ${engine}で成功: ${selectedTags.length}個のタグ選択`)
      break
    } catch (error: any) {
      lastError = error
      console.log(`❌ ${engine}で失敗: ${error.message}`)
      
      if (engine !== engines[engines.length - 1]) {
        console.log(`🔄 次のエンジンにフォールバック...`)
        continue
      }
    }
  }

  // 全エンジンが失敗した場合はエラー
  if (selectedTags.length === 0 && lastError) {
    throw new Error(`全てのAIエンジンでタグ選択に失敗しました: ${lastError.message}`)
  }

  // 10-15個の範囲に調整
  if (selectedTags.length < 10) {
    const remainingCandidates = approvedCandidates.filter(c => !selectedTags.includes(c))
    const additionalTags = remainingCandidates.slice(0, 10 - selectedTags.length)
    selectedTags.push(...additionalTags)
    console.log(`⚠️ タグ数が不足していたため、${additionalTags.length}個追加しました`)
  } else if (selectedTags.length > 15) {
    selectedTags = selectedTags.slice(0, 15)
    console.log(`⚠️ タグ数が超過していたため、15個に制限しました`)
  }

  const processingTime = Date.now() - startTime
  console.log(`✅ タグ選択完了: ${selectedTags.length}個, 処理時間: ${processingTime}ms`)

  return { tags: selectedTags, processingTime }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const videoData: VideoData[] = body.data || []
    const approvedCandidates: string[] = body.approved_candidates || []
    const aiEngine = body.ai_engine || 'openai'
    const batchIndex = body.batch_index || 0
    const batchSize = body.batch_size || 20

    if (!videoData.length) {
      return NextResponse.json({
        success: false,
        error: '動画データがありません'
      }, { status: 400 })
    }

    if (!approvedCandidates.length) {
      return NextResponse.json({
        success: false,
        error: '承認されたタグ候補がありません',
        message: 'まず /api/ai/stage1 でタグ候補を生成し、内容を確認してから第2段階を実行してください'
      }, { status: 400 })
    }

    const startTime = Date.now()
    
    // バッチ処理のための範囲計算
    const startIdx = batchIndex * batchSize
    const endIdx = Math.min(startIdx + batchSize, videoData.length)
    const batchData = videoData.slice(startIdx, endIdx)
    const results = []

    console.log(`バッチ処理: ${startIdx}-${endIdx}/${videoData.length}件`)

    // バッチ内の各動画をLLMで順次処理
    for (let i = 0; i < batchData.length; i++) {
      const video = batchData[i]
      const videoIndex = startIdx + i
      
      console.log(`🎬 動画 ${videoIndex + 1}/${videoData.length}: "${video.title.slice(0, 50)}..." 処理開始`)
      
      try {
        const result = await selectTagsForVideoWithAI(video, approvedCandidates, aiEngine)
        
        results.push({
          video_index: videoIndex,
          title: video.title,
          selected_tags: result.tags,
          tag_count: result.tags.length,
          processing_time_ms: result.processingTime,
          confidence: 1.0, // LLMベースなので信頼度は高く設定
          success: true
        })
        
        console.log(`✅ 動画 ${videoIndex + 1} 完了: ${result.tags.length}個のタグ選択 (${result.processingTime}ms)`)
        
      } catch (error: any) {
        console.error(`❌ 動画 ${videoIndex + 1} エラー: ${error.message}`)
        
        results.push({
          video_index: videoIndex,
          title: video.title,
          selected_tags: [],
          tag_count: 0,
          processing_time_ms: 0,
          confidence: 0.0,
          success: false,
          error: error.message
        })
      }
      
      // レート制限回避のため動画間に少し間隔を設ける
      if (i < batchData.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // 1秒待機
      }
    }

    const processingTime = (Date.now() - startTime) / 1000
    const isLastBatch = endIdx >= videoData.length
    const totalBatches = Math.ceil(videoData.length / batchSize)

    return NextResponse.json({
      stage: 2,
      success: true,
      batch_info: {
        current_batch: batchIndex,
        total_batches: totalBatches,
        batch_size: batchSize,
        processed_in_batch: results.length,
        is_last_batch: isLastBatch
      },
      results: results,
      statistics: {
        batch_videos: batchData.length,
        total_videos: videoData.length,
        processing_time: processingTime
      },
      message: isLastBatch ? 
        `全${videoData.length}件の処理が完了しました` : 
        `バッチ${batchIndex + 1}/${totalBatches}の処理が完了しました`
    })

  } catch (error: any) {
    console.error('Stage2 API error:', error)
    return NextResponse.json({
      success: false,
      error: `第2段階処理エラー: ${error.message}`,
      stage: 2
    }, { status: 500 })
  }
}