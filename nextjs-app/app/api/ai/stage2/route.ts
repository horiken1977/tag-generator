import { NextRequest, NextResponse } from 'next/server'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 30

interface VideoData {
  title: string
  skill: string
  description: string
  summary: string
  transcript: string
}

function selectTagsForVideo(video: VideoData, approvedCandidates: string[]): string[] {
  const selectedTags: string[] = []
  
  // 動画の全テキストを結合（文字起こし含む）
  const fullText = [
    video.title,
    video.skill,
    video.description,
    video.summary,
    video.transcript
  ].join(' ').toLowerCase()

  // 承認されたタグ候補から、動画の内容に含まれるものを選択
  approvedCandidates.forEach(candidate => {
    if (fullText.includes(candidate.toLowerCase())) {
      selectedTags.push(candidate)
    }
  })

  // 最低限のタグ数を確保（10個）
  if (selectedTags.length < 10) {
    const remainingCandidates = approvedCandidates.filter(c => !selectedTags.includes(c))
    const additionalTags = remainingCandidates.slice(0, 10 - selectedTags.length)
    selectedTags.push(...additionalTags)
  }

  // 最大15個に制限
  return selectedTags.slice(0, 15)
}

function calculateConfidence(selectedTags: string[], video: VideoData): number {
  if (!selectedTags.length) return 0

  // 文字起こしとの関連度をチェック
  const transcript = video.transcript.toLowerCase()
  let relatedCount = 0
  
  selectedTags.forEach(tag => {
    if (transcript.includes(tag.toLowerCase())) {
      relatedCount++
    }
  })

  const transcriptRelevance = transcript ? relatedCount / selectedTags.length : 0.5
  const tagCountFactor = Math.min(1.0, selectedTags.length / 12.0)
  
  return Math.round((transcriptRelevance * 0.7 + tagCountFactor * 0.3) * 100) / 100
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

    // バッチ内の各動画を処理
    for (let i = 0; i < batchData.length; i++) {
      const video = batchData[i]
      const selectedTags = selectTagsForVideo(video, approvedCandidates)
      const confidence = calculateConfidence(selectedTags, video)

      results.push({
        video_index: startIdx + i,
        title: video.title,
        selected_tags: selectedTags,
        tag_count: selectedTags.length,
        confidence: confidence
      })
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