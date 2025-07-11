import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 30

interface VideoData {
  title?: string
  skill?: string
  description?: string
  summary?: string
  transcript?: string
}

function extractKeywords(text: string): string[] {
  const keywords: string[] = []
  
  // 英語の大文字で始まる単語（2文字以上）
  const englishWords = text.match(/[A-Z][a-zA-Z]+/g) || []
  englishWords.forEach(word => {
    if (word.length >= 2) keywords.push(word)
  })
  
  // 全て大文字のアクロニム（2-6文字）
  const acronyms = text.match(/\b[A-Z]{2,6}\b/g) || []
  acronyms.forEach(word => keywords.push(word))
  
  // カタカナ語（2文字以上）
  const katakanaWords = text.match(/[ァ-ヶー]+/g) || []
  katakanaWords.forEach(word => {
    if (word.length >= 2) keywords.push(word)
  })
  
  // 漢字2文字以上
  const kanjiWords = text.match(/[一-龯]{2,}/g) || []
  kanjiWords.forEach(word => {
    if (word.length >= 2 && word.length <= 8) keywords.push(word)
  })
  
  // ひらがな・漢字混合の専門用語（3文字以上）
  const mixedWords = text.match(/[ひらがな漢字]{3,}/g) || []
  mixedWords.forEach(word => {
    if (word.length >= 3 && word.length <= 10) keywords.push(word)
  })
  
  // 英数字混合（Excel、Office365など）
  const alphanumeric = text.match(/[A-Za-z]+\d+|[A-Za-z]*\d+[A-Za-z]+/g) || []
  alphanumeric.forEach(word => {
    if (word.length >= 3) keywords.push(word)
  })
  
  return keywords
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
  // テキストサイズを制限
  if (allText.length > 15000) {
    allText = allText.slice(0, 15000)
    console.log('⚠️ テキストサイズを15000文字に制限しました')
  }
  
  console.log(`全テキスト文字数: ${allText.length}`)

  // AI API使用可能かチェック
  const useAI = process.env.OPENAI_API_KEY || process.env.CLAUDE_API_KEY || process.env.GEMINI_API_KEY
  let keywords: string[] = []

  if (useAI) {
    // AI APIでタグ生成
    try {
      const aiClient = new AIClient()
      const aiEngine = process.env.OPENAI_API_KEY ? 'openai' : 
                     process.env.CLAUDE_API_KEY ? 'claude' : 'gemini'
      keywords = await aiClient.generateTags(allText, aiEngine)
      console.log(`AI生成完了 (${aiEngine}): ${keywords.length}個のタグ`)
    } catch (error) {
      console.error('AI生成失敗、フォールバック:', error)
      keywords = extractKeywords(allText)
    }
  } else {
    // フォールバック: キーワード抽出
    keywords = extractKeywords(allText)
  }

  // 事前定義キーワードは削除 - 純粋にデータから抽出

  // 重複除去
  keywords = [...new Set(keywords)]

  // 汎用語フィルタリング（緩和）
  const genericWords = [
    'について', 'による', 'ため', 'こと', 'もの', 'など',
    'です', 'ます', 'した', 'する', 'なる', 'ある'
  ]

  const filteredKeywords = keywords.filter(keyword => {
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

  // 最大200個（当初仕様通り）
  const finalKeywords = filteredKeywords.slice(0, 200)
  
  console.log(`生成されたキーワード数: ${keywords.length}, フィルタ後: ${filteredKeywords.length}, 最終: ${finalKeywords.length}`)

  return finalKeywords
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const videoData: VideoData[] = body.data || []
    const batchIndex = body.batch_index ?? null
    const batchSize = body.batch_size || 100
    const allBatchTexts = body.all_batch_texts || []
    
    if (!videoData.length) {
      return NextResponse.json({
        success: false,
        error: '動画データがありません'
      }, { status: 400 })
    }

    // バッチ処理の場合
    if (batchIndex !== null) {
      // バッチデータの処理
      const startIdx = batchIndex * batchSize
      const endIdx = Math.min(startIdx + batchSize, videoData.length)
      const processData = videoData.slice(startIdx, endIdx)
      
      console.log(`Stage1 バッチ処理: ${startIdx}-${endIdx}/${videoData.length}件`)
      
      // このバッチのテキストを収集
      const batchTexts = collectBatchTexts(processData)
      
      const isLastBatch = endIdx >= videoData.length
      const totalBatches = Math.ceil(videoData.length / batchSize)
      
      if (isLastBatch) {
        // 最後のバッチ: 全バッチのテキストを結合してタグ生成
        const allTexts = [...allBatchTexts, batchTexts].join(' ')
        const keywords = await generateTagCandidates(allTexts)
        
        return NextResponse.json({
          stage: 1,
          success: true,
          tag_candidates: keywords,
          candidate_count: keywords.length,
          batch_info: {
            current_batch: batchIndex,
            total_batches: totalBatches,
            is_last_batch: true
          },
          message: `全${videoData.length}件の分析からタグ候補を生成しました`
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

    // 従来の一括処理（後方互換性）
    const processData = videoData

    // データ集約（文字起こし除外）
    const allTitles: string[] = []
    const allSkills: string[] = []
    const allDescriptions: string[] = []
    const allSummaries: string[] = []

    processData.forEach(video => {
      if (video.title) allTitles.push(video.title.slice(0, 200)) // 最大200文字に増加
      if (video.skill) allSkills.push(video.skill.slice(0, 100))   // 最大100文字に増加
      if (video.description) allDescriptions.push(video.description.slice(0, 300)) // 最大300文字に増加
      if (video.summary) allSummaries.push(video.summary.slice(0, 400)) // 最大400文字に増加
    })

    // 全テキストを結合（サイズ制限）
    let allText = [
      ...allTitles,
      ...allSkills,
      ...allDescriptions,
      ...allSummaries
    ].join(' ')

    // テキストサイズをさらに制限（Vercel APIボディサイズ対応）
    if (allText.length > 15000) {
      allText = allText.slice(0, 15000)
      console.log('⚠️ テキストサイズを15000文字に制限しました')
    }
    
    console.log(`全テキスト文字数: ${allText.length}, 処理対象動画数: ${processData.length}`)

    // AI API使用可能かチェック
    const useAI = process.env.OPENAI_API_KEY || process.env.CLAUDE_API_KEY || process.env.GEMINI_API_KEY
    let keywords: string[] = []

    if (useAI) {
      // AI APIでタグ生成
      try {
        const aiClient = new AIClient()
        const aiEngine = process.env.OPENAI_API_KEY ? 'openai' : 
                       process.env.CLAUDE_API_KEY ? 'claude' : 'gemini'
        keywords = await aiClient.generateTags(allText, aiEngine)
        console.log(`AI生成完了 (${aiEngine}): ${keywords.length}個のタグ`)
      } catch (error) {
        console.error('AI生成失敗、フォールバック:', error)
        keywords = extractKeywords(allText)
      }
    } else {
      // フォールバック: キーワード抽出
      keywords = extractKeywords(allText)
    }

    // 事前定義キーワードは削除 - 純粋にデータから抽出

    // 重複除去
    keywords = [...new Set(keywords)]

    // 汎用語フィルタリング（緩和）
    const genericWords = [
      'について', 'による', 'ため', 'こと', 'もの', 'など',
      'です', 'ます', 'した', 'する', 'なる', 'ある'
    ]

    const filteredKeywords = keywords.filter(keyword => {
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

    // 最大200個（当初仕様通り）
    const finalKeywords = filteredKeywords.slice(0, 200)
    
    console.log(`生成されたキーワード数: ${keywords.length}, フィルタ後: ${filteredKeywords.length}, 最終: ${finalKeywords.length}`)

    return NextResponse.json({
      stage: 1,
      success: true,
      tag_candidates: finalKeywords,
      candidate_count: finalKeywords.length,
      processing_time: 0.5,
      source_data_stats: {
        total_videos: processData.length,
        titles_processed: allTitles.length,
        skills_processed: allSkills.length,
        descriptions_processed: allDescriptions.length,
        summaries_processed: allSummaries.length,
        transcripts_excluded: true
      },
      message: 'タグ候補が生成されました。内容を確認して承認してください。'
    })

  } catch (error: any) {
    console.error('Stage1 API error:', error)
    return NextResponse.json({
      success: false,
      error: `第1段階処理エラー: ${error.message}`,
      stage: 1
    }, { status: 500 })
  }
}