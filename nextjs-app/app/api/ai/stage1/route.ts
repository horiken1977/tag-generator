import { NextRequest, NextResponse } from 'next/server'

interface VideoData {
  title?: string
  skill?: string
  description?: string
  summary?: string
  transcript?: string
}

function extractKeywords(text: string): string[] {
  const keywords: string[] = []
  
  // 英語の大文字で始まる単語
  const englishWords = text.match(/[A-Z][a-zA-Z]*/g) || []
  englishWords.forEach(word => {
    if (word.length >= 3) keywords.push(word)
  })
  
  // カタカナ語
  const katakanaWords = text.match(/[ァ-ヶー]+/g) || []
  katakanaWords.forEach(word => {
    if (word.length >= 3) keywords.push(word)
  })
  
  // 漢字2文字以上
  const kanjiWords = text.match(/[一-龯]{2,}/g) || []
  kanjiWords.forEach(word => {
    if (word.length >= 2) keywords.push(word)
  })
  
  return keywords
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const videoData: VideoData[] = body.data || []
    
    if (!videoData.length) {
      return NextResponse.json({
        success: false,
        error: '動画データがありません'
      }, { status: 400 })
    }

    // バッチサイズ制限
    const maxBatchSize = 50
    const processData = videoData.slice(0, maxBatchSize)

    // データ集約（文字起こし除外）
    const allTitles: string[] = []
    const allSkills: string[] = []
    const allDescriptions: string[] = []
    const allSummaries: string[] = []

    processData.forEach(video => {
      if (video.title) allTitles.push(video.title)
      if (video.skill) allSkills.push(video.skill)
      if (video.description) allDescriptions.push(video.description)
      if (video.summary) allSummaries.push(video.summary)
    })

    // 全テキストを結合
    const allText = [
      ...allTitles,
      ...allSkills,
      ...allDescriptions,
      ...allSummaries
    ].join(' ')

    // キーワード抽出
    let keywords = extractKeywords(allText)

    // 既知の重要キーワードを追加
    const importantKeywords = [
      'Google Analytics', 'ROI', 'CPA', 'PDCAサイクル',
      'Instagram', 'Facebook', 'Twitter', 'TikTok', 'YouTube',
      'SEO', 'SEM', 'KPI', 'OKR', 'A/Bテスト',
      'エンゲージメント率', 'コンバージョン率', 'CTR', 'CPM', 'ROAS',
      'マーケティング', 'ブランディング', 'プロモーション',
      'データ分析', 'アナリティクス', 'レポート作成'
    ]

    importantKeywords.forEach(keyword => {
      if (allText.includes(keyword)) {
        keywords.push(keyword)
      }
    })

    // 重複除去
    keywords = [...new Set(keywords)]

    // 汎用語フィルタリング
    const genericWords = [
      '要素', '分類', 'ポイント', '手法', '方法', '技術',
      '基本', '応用', '実践', '理論', '概要', '入門',
      'について', 'による', 'ため', 'こと', 'もの'
    ]

    const filteredKeywords = keywords.filter(keyword => {
      // 汎用語を含むか確認
      const isGeneric = genericWords.some(generic => keyword.includes(generic))
      // 数字+つの パターンを除外
      const hasNumberPattern = /\d+つの/.test(keyword)
      // 短すぎる単語を除外
      const tooShort = keyword.length < 2
      
      return !isGeneric && !hasNumberPattern && !tooShort
    })

    // 最大30個に制限
    const finalKeywords = filteredKeywords.slice(0, 30)

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