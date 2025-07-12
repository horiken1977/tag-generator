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

async function generateTagCandidates(allText: string): Promise<string[]> {
  console.log(`📊 全テキスト文字数: ${allText.length} (450件の動画データ統合分析)`)
  
  // 適度な制限を設定（完全無制限ではVercelで問題が起きる可能性）
  if (allText.length > 80000) {
    const originalLength = allText.length
    allText = allText.slice(0, 80000)
    console.log(`⚠️ テキストサイズを${originalLength}文字から80000文字に調整しました`)
  }

  // AI API環境変数の詳細チェック
  const hasOpenAI = !!process.env.OPENAI_API_KEY
  const hasClaude = !!process.env.CLAUDE_API_KEY
  const hasGemini = !!process.env.GEMINI_API_KEY
  
  console.log(`🔍 AI環境変数チェック: OpenAI=${hasOpenAI}, Claude=${hasClaude}, Gemini=${hasGemini}`)
  
  // AI APIが設定されていない場合はエラー
  if (!hasOpenAI && !hasClaude && !hasGemini) {
    throw new Error('AI APIキーが設定されていません。OpenAI、Claude、またはGeminiのAPIキーを設定してください。')
  }
  
  // AI APIでタグ生成を実行
  console.log('🤖 AI分析開始 - LLMでタグ候補を生成中...')
  console.log(`📝 分析対象テキスト: "${allText.slice(0, 100)}..."`)
  
  const startTime = Date.now()
  const aiClient = new AIClient()
  const aiEngine = hasOpenAI ? 'openai' : hasClaude ? 'claude' : 'gemini'
  
  console.log(`🎯 使用AIエンジン: ${aiEngine}`)
  console.log('⏳ AI API呼び出し中...')
  
  const keywords = await aiClient.generateTags(allText, aiEngine)
  
  const processingTime = Date.now() - startTime
  console.log(`✅ AI生成完了 (${aiEngine}): ${keywords.length}個のタグ, 処理時間: ${processingTime}ms`)
  console.log(`🏷️ 生成されたタグ例: ${keywords.slice(0, 5).join(', ')}`)

  // 重複除去
  const uniqueKeywords = [...new Set(keywords)]

  // 汎用語フィルタリング（緩和）
  const genericWords = [
    'について', 'による', 'ため', 'こと', 'もの', 'など',
    'です', 'ます', 'した', 'する', 'なる', 'ある'
  ]

  const filteredKeywords = uniqueKeywords.filter(keyword => {
    // 明らかに不要な汎用語のみ除外
    const isGeneric = genericWords.some(generic => keyword.endsWith(generic) || keyword === generic)
    // 数字+つの パターンを除外
    const hasNumberPattern = /\d+つの/.test(keyword)
    // 短すぎる単語を除外
    const tooShort = keyword.length < 2
    // 1文字の助詞・記号を除外
    const isSingleChar = /^[はがをでにへとのもやかからまで]$/.test(keyword)
    
    return !isGeneric && !hasNumberPattern && !tooShort && !isSingleChar
  })

  // 制限解除 - LLMからの全タグを使用
  const finalKeywords = filteredKeywords
  
  console.log(`生成されたキーワード数: ${keywords.length}, フィルタ後: ${filteredKeywords.length}, 最終: ${finalKeywords.length}`)

  return finalKeywords
}

export async function POST(request: NextRequest) {
  console.log('🚀 Stage1 API開始')
  try {
    const body = await request.json()
    const videoData: VideoData[] = body.data || []
    const batchIndex = body.batch_index ?? null
    const batchSize = body.batch_size || 100
    const allBatchTexts = body.all_batch_texts || []
    const totalDataLength = body.total_data_length || videoData.length
    
    console.log(`📊 リクエスト解析: videoData=${videoData.length}件, batchIndex=${batchIndex}, totalDataLength=${totalDataLength}`)
    
    if (!videoData.length) {
      return NextResponse.json({
        success: false,
        error: '動画データがありません'
      }, { status: 400 })
    }

    // バッチ処理の場合
    if (batchIndex !== null) {
      // このバッチのデータを処理（クライアントから既に切り出し済み）
      const processData = videoData
      
      console.log(`Stage1 バッチ処理: バッチ${batchIndex}, 受信データ=${videoData.length}件, 総データ=${totalDataLength}件`)
      
      // このバッチのテキストを収集
      const batchTexts = collectBatchTexts(processData)
      
      // 総件数を基準にバッチ判定（重要！）
      const totalBatches = Math.ceil(totalDataLength / batchSize)
      const isLastBatch = batchIndex === totalBatches - 1
      
      console.log(`バッチ判定: batchIndex=${batchIndex}, totalDataLength=${totalDataLength}, isLastBatch=${isLastBatch}, totalBatches=${totalBatches}`)
      
      if (isLastBatch) {
        // 最後のバッチ: 全バッチのテキストを結合してタグ生成
        console.log(`🔄 最後のバッチ処理開始: 蓄積バッチ数=${allBatchTexts.length}, 現在バッチテキスト長=${batchTexts.length}`)
        
        const allTexts = [...allBatchTexts, batchTexts].join(' ')
        console.log(`📊 全バッチ完了: 総テキスト長=${allTexts.length}文字, バッチ数=${allBatchTexts.length + 1}`)
        
        // メモリとサイズチェック
        const textSizeMB = allTexts.length / 1024 / 1024
        console.log(`💾 統合テキストサイズ: ${textSizeMB.toFixed(2)}MB`)
        
        if (allTexts.length > 200000) {
          console.log(`⚠️ テキストサイズ警告: ${allTexts.length}文字は大きすぎる可能性があります`)
        }
        
        console.log(`🤖 LLM分析開始: 全${totalDataLength}件のデータを統合分析中...`)
        
        const startTime = Date.now()
        let keywords: string[]
        let processingTime: number
        
        try {
          keywords = await generateTagCandidates(allTexts)
          processingTime = Date.now() - startTime
          
          console.log(`✅ LLM分析完了: ${keywords.length}個のタグ生成, 処理時間: ${processingTime}ms`)
        } catch (llmError: any) {
          console.error(`❌ LLM分析エラー:`, {
            message: llmError.message,
            name: llmError.name,
            textLength: allTexts.length
          })
          throw llmError
        }
        
        return NextResponse.json({
          stage: 1,
          success: true,
          tag_candidates: keywords,
          candidate_count: keywords.length,
          processing_time: processingTime / 1000, // Convert to seconds
          batch_info: {
            current_batch: batchIndex,
            total_batches: totalBatches,
            is_last_batch: true,
            total_text_length: allTexts.length,
            processed_videos: totalDataLength
          },
          source_data_stats: {
            total_videos: totalDataLength,
            total_batches: totalBatches,
            transcripts_excluded: true
          },
          message: `全${totalDataLength}件の分析からタグ候補を生成しました（処理時間: ${(processingTime/1000).toFixed(1)}秒）`
        })
      } else {
        // 中間バッチ: テキストを収集して返す
        return NextResponse.json({
          stage: 1,
          success: true,
          batch_text: batchTexts,
          batch_info: {
            current_batch: batchIndex,
            total_batches: totalBatches,
            is_last_batch: false
          },
          message: `バッチ${batchIndex + 1}/${totalBatches}の処理が完了しました`
        })
      }
    }

    // 一括処理は廃止、バッチ処理のみをサポート
    return NextResponse.json({
      success: false,
      error: 'バッチ処理パラメータが必要です。batch_indexを指定してください。',
      stage: 1
    }, { status: 400 })

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