// AI API client for tag generation

interface AIResponse {
  success: boolean
  tags?: string[]
  error?: string
}

export class AIClient {
  private baseUrl = 'https://api.openai.com/v1/chat/completions'
  
  async generateTags(content: string, engine: string = 'openai'): Promise<string[]> {
    if (engine === 'openai') {
      return await this.callOpenAI(content)
    } else if (engine === 'claude') {
      return await this.callClaude(content)
    } else if (engine === 'gemini') {
      return await this.callGemini(content)
    }
    
    throw new Error(`Unsupported AI engine: ${engine}`)
  }

  // Stage1A: 軽量キーワード抽出（1行ずつ）
  async extractKeywordsLight(content: string, engine: string = 'openai'): Promise<string[]> {
    if (engine === 'openai') {
      return await this.callOpenAI(content, 'light')
    } else if (engine === 'claude') {
      return await this.callClaude(content, 'light')
    } else if (engine === 'gemini') {
      return await this.callGemini(content, 'light')
    }
    
    throw new Error(`Unsupported AI engine: ${engine}`)
  }

  // Stage1B: 全体最適化
  async optimizeTags(keywords: string[], engine: string = 'openai'): Promise<string[]> {
    const keywordString = keywords.join(', ')
    
    if (engine === 'openai') {
      return await this.callOpenAI(keywordString, 'optimize')
    } else if (engine === 'claude') {
      return await this.callClaude(keywordString, 'optimize')
    } else if (engine === 'gemini') {
      return await this.callGemini(keywordString, 'optimize')
    }
    
    throw new Error(`Unsupported AI engine: ${engine}`)
  }
  
  private async callOpenAI(content: string, promptType: 'standard' | 'light' | 'optimize' = 'standard'): Promise<string[]> {
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      throw new Error('OpenAI API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else {
      prompt = this.buildPrompt(content)
    }
    console.log(`🤖 OpenAI API呼び出し開始 - プロンプト長: ${prompt.length}文字, コンテンツ長: ${content.length}文字`)
    
    const startTime = Date.now()
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 2000,
        temperature: 0.3
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ OpenAI API HTTP error: ${response.status}`)
      console.error(`Response headers:`, Object.fromEntries(response.headers.entries()))
      console.error(`Error body:`, errorText)
      
      let errorMessage = `OpenAI API error: ${response.status}`
      try {
        const errorData = JSON.parse(errorText)
        if (errorData.error?.message) {
          errorMessage += ` - ${errorData.error.message}`
        } else {
          errorMessage += ` - ${errorText}`
        }
      } catch {
        errorMessage += ` - ${errorText}`
      }
      
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    const result = data.choices[0]?.message?.content || ''
    const processingTime = Date.now() - startTime
    
    console.log(`✅ OpenAI API応答完了 - 処理時間: ${processingTime}ms, レスポンス長: ${result.length}文字`)
    console.log(`📝 OpenAI生成内容プレビュー: "${result.substring(0, 200)}..."`)
    
    return this.parseTagsFromResponse(result)
  }
  
  private async callClaude(content: string, promptType: 'standard' | 'light' | 'optimize' = 'standard'): Promise<string[]> {
    const apiKey = process.env.CLAUDE_API_KEY
    if (!apiKey) {
      throw new Error('Claude API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else {
      prompt = this.buildPrompt(content)
    }
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-3-haiku-20240307',
        max_tokens: 2000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ Claude API HTTP error: ${response.status}`)
      console.error(`Error body:`, errorText)
      throw new Error(`Claude API error: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    const result = data.content[0]?.text || ''
    
    console.log(`🤖 Claude API応答 (${promptType}): "${result}"`)
    
    const tags = this.parseTagsFromResponse(result)
    
    // デバッグ用：parseTagsFromResponseの前後を確認
    if (tags.length === 0 && result.length > 0) {
      console.log(`⚠️ Claude応答はあったが、タグが0個になりました。応答内容: "${result}"`)
    }
    
    return tags
  }
  
  private async callGemini(content: string, promptType: 'standard' | 'light' | 'optimize' = 'standard'): Promise<string[]> {
    const apiKey = process.env.GEMINI_API_KEY
    if (!apiKey) {
      throw new Error('Gemini API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else {
      prompt = this.buildPrompt(content)
    }
    
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: prompt
              }
            ]
          }
        ],
        generationConfig: {
          temperature: 0.3,
          maxOutputTokens: 2000
        }
      })
    })
    
    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`)
    }
    
    const data = await response.json()
    const result = data.candidates[0]?.content?.parts[0]?.text || ''
    
    return this.parseTagsFromResponse(result)
  }
  
  private buildPrompt(content: string): string {
    return `
以下は400-450件のマーケティング動画データの統合分析です。このデータ全体を深く分析して、具体的で検索に有用なタグを150-200個生成してください。

【全動画データ】:
${content}

【重要な指示】:
- 400-450件の動画データ全体を分析対象とする
- 多様性を重視し、異なる分野・手法・ツールから幅広くタグを抽出
- 150-200個の豊富なタグ候補を生成する

【タグ生成の基準】:
1. 具体的なツール名・サービス名・手法名（Google Analytics、Instagram、Facebook、LinkedIn、YouTube等）
2. 業界固有の概念・理論・フレームワーク（PDCA、SWOT、4P、カスタマージャーニー等）
3. 測定可能な指標名・KPI（ROI、CPA、CTR、エンゲージメント率、コンバージョン率等）
4. 具体的なプロセス名・手順名（A/Bテスト、セグメンテーション、ターゲティング等）
5. 職種・業界・分野名（デジタルマーケティング、SNSマーケティング、コンテンツマーケティング等）
6. 技術・プラットフォーム名（SEO、SEM、API、CRM等）

【絶対に避けるべき汎用語】:
- 「6つの要素」「8つの分類」「4つのポイント」等の数字+汎用語
- 「要素」「分類」「ポイント」「手法」「方法」「技術」等の単体使用
- 「基本」「応用」「実践」「理論」「概要」「入門」等の抽象表現

出力形式: 具体的で有用なタグのみをカンマ区切りで150-200個出力してください。1行ずつではなく、カンマ区切りで連続して出力してください。
`
  }

  // Stage1A: 軽量キーワード抽出用プロンプト
  private buildLightPrompt(content: string): string {
    return `
以下のマーケティング動画の1行データから、検索に有用なキーワードを20-30個抽出してください。

【動画データ】:
${content}

【抽出基準】:
1. 具体的なツール名・サービス名（Google Analytics、Facebook、Instagram、LinkedIn、YouTube等）
2. 業界用語・専門用語（マーケティング、デジタル、オンライン、SEO、SEM等）
3. 測定指標・KPI名（ROI、CPA、CTR、コンバージョン率、エンゲージメント等）
4. 重要な概念・手法名（A/Bテスト、セグメンテーション、ターゲティング等）
5. 職種・役職名（マーケター、アナリスト、PM等）
6. 業界・分野名（EC、B2B、B2C、SaaS等）
7. 技術・プラットフォーム名（API、CRM、MA、CDP等）
8. スキル・能力名（分析、戦略、企画、運用等）

【避けるべき語】:
- 助詞・接続詞・一般的すぎる語（「する」「ある」「方法」「技術」等の単体使用）
- 「6つの」「8つの」等の数量表現のみ

出力: 検索に有用で具体的なキーワードを20-30個、カンマ区切りで出力してください。多様性を重視し、幅広い観点から抽出してください。
`
  }

  // Stage1B: 全体最適化用プロンプト
  private buildOptimizePrompt(keywords: string[]): string {
    // キーワードテキストが長すぎる場合は制限
    let keywordText = keywords.join(', ')
    const maxLength = 50000 // 50KB制限
    
    if (keywordText.length > maxLength) {
      console.log(`⚠️ キーワードテキストが長すぎます (${keywordText.length}文字)。切り詰めます。`)
      // 最初のN個のキーワードだけを使用
      let truncatedKeywords = []
      let currentLength = 0
      for (const keyword of keywords) {
        if (currentLength + keyword.length + 2 > maxLength) break
        truncatedKeywords.push(keyword)
        currentLength += keyword.length + 2 // カンマとスペース
      }
      keywordText = truncatedKeywords.join(', ')
      console.log(`✂️ ${truncatedKeywords.length}個のキーワードに制限 (${keywordText.length}文字)`);
    }
    
    return `
以下は450件のマーケティング動画から抽出された${keywords.length}個のキーワードです。これらを統合・整理して、重複を排除し、最も重要で検索に有用な200個のタグを生成してください。

【収集されたキーワード】:
${keywordText}

【統合・最適化の指示】:
1. 同じ概念の異なる表現を統合（例：「デジタルマーケティング」「オンラインマーケティング」→「デジタルマーケティング」）
2. 重要度と出現頻度を考慮した優先順位付け
3. 全体のバランスを取り、多様な分野をカバー
4. 具体性と検索有用性を重視

【出力要求】:
- 200個の最適化されたタグ
- 重複なし
- 具体的で検索に有用
- カンマ区切りで出力

出力: 最適化された200個のタグをカンマ区切りで出力してください。
`
  }
  
  private parseTagsFromResponse(response: string): string[] {
    // Extract tags from AI response - expecting 150-200 tags
    const splitTags = response.split(/[,\n]/)
    const trimmedTags = splitTags.map(tag => tag.trim())
    const nonEmptyTags = trimmedTags.filter(tag => tag.length > 0)
    const filteredTags = nonEmptyTags.filter(tag => !this.isGenericTag(tag))
    const finalTags = filteredTags.slice(0, 300) // 最大300個に制限（通常は200個程度）
    
    console.log(`🏷️ タグ解析詳細: 分割=${splitTags.length}, 空除去=${nonEmptyTags.length}, 汎用語除去=${filteredTags.length}, 最終=${finalTags.length}`)
    
    // デバッグ：汎用語としてフィルタされたタグを表示
    if (nonEmptyTags.length > filteredTags.length) {
      const genericTags = nonEmptyTags.filter(tag => this.isGenericTag(tag))
      console.log(`🚫 汎用語として除外されたタグ: ${genericTags.join(', ')}`)
    }
    
    return finalTags
  }
  
  private isGenericTag(tag: string): boolean {
    const genericPatterns = [
      // 数字+汎用語のパターンのみ（具体的な指定）
      /\d+つの要素/,
      /\d+つの分類/,
      /\d+つのポイント/,
      /\d+つの手法/,
      /\d+つの方法/,
      /\d+個の要素/,
      /\d+個の分類/,
      /\d+個のポイント/,
      /\d+個の手法/,
      /\d+個の方法/,
      /\d+つのステージ/,
      /\d+流派/,
      // 単体での汎用語
      /^要素$/,
      /^分類$/,
      /^ポイント$/,
      /^手法$/,
      /^方法$/,
      /^基本$/,
      /^応用$/,
      /^実践$/,
      /^理論$/,
      /^概要$/,
      /^入門$/
    ]
    
    return genericPatterns.some(pattern => pattern.test(tag))
  }
  
}