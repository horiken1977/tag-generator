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
    const prompt = this.buildLightPrompt(content)
    
    if (engine === 'openai') {
      return await this.callOpenAI(prompt)
    } else if (engine === 'claude') {
      return await this.callClaude(prompt)
    } else if (engine === 'gemini') {
      return await this.callGemini(prompt)
    }
    
    throw new Error(`Unsupported AI engine: ${engine}`)
  }

  // Stage1B: 全体最適化
  async optimizeTags(keywords: string[], engine: string = 'openai'): Promise<string[]> {
    const prompt = this.buildOptimizePrompt(keywords)
    
    if (engine === 'openai') {
      return await this.callOpenAI(prompt)
    } else if (engine === 'claude') {
      return await this.callClaude(prompt)
    } else if (engine === 'gemini') {
      return await this.callGemini(prompt)
    }
    
    throw new Error(`Unsupported AI engine: ${engine}`)
  }
  
  private async callOpenAI(content: string): Promise<string[]> {
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      throw new Error('OpenAI API key not configured')
    }
    
    const prompt = this.buildPrompt(content)
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
      console.error(`❌ OpenAI API HTTP error: ${response.status}, body: ${errorText}`)
      throw new Error(`OpenAI API error: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    const result = data.choices[0]?.message?.content || ''
    const processingTime = Date.now() - startTime
    
    console.log(`✅ OpenAI API応答完了 - 処理時間: ${processingTime}ms, レスポンス長: ${result.length}文字`)
    console.log(`📝 OpenAI生成内容プレビュー: "${result.substring(0, 200)}..."`)
    
    return this.parseTagsFromResponse(result)
  }
  
  private async callClaude(content: string): Promise<string[]> {
    const apiKey = process.env.CLAUDE_API_KEY
    if (!apiKey) {
      throw new Error('Claude API key not configured')
    }
    
    const prompt = this.buildPrompt(content)
    
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
      throw new Error(`Claude API error: ${response.status}`)
    }
    
    const data = await response.json()
    const result = data.content[0]?.text || ''
    
    return this.parseTagsFromResponse(result)
  }
  
  private async callGemini(content: string): Promise<string[]> {
    const apiKey = process.env.GEMINI_API_KEY
    if (!apiKey) {
      throw new Error('Gemini API key not configured')
    }
    
    const prompt = this.buildPrompt(content)
    
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
以下のマーケティング動画の1行データから、重要なキーワードを3-5個抽出してください。

【動画データ】:
${content}

【抽出基準】:
- 具体的なツール名・サービス名
- 業界用語・専門用語
- 測定指標・KPI名
- 重要な概念・手法名

【避けるべき語】:
- 汎用的すぎる語（「方法」「技術」等）
- 助詞・接続詞

出力: 最も重要なキーワードのみをカンマ区切りで3-5個出力してください。重複を避け、簡潔に。
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
    const tags = response
      .split(/[,\n]/)
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)
      .filter(tag => !this.isGenericTag(tag))
      .slice(0, 300) // 最大300個に制限（通常は200個程度）
    
    console.log(`🏷️ AIから受信したタグ数: ${tags.length}`)
    return tags
  }
  
  private isGenericTag(tag: string): boolean {
    const genericPatterns = [
      /\d+つの/,
      /\d+個の/,
      /\d+の/,
      /^要素$/,
      /^分類$/,
      /^ポイント$/,
      /^手法$/,
      /^方法$/,
      /^基本$/,
      /^応用$/
    ]
    
    return genericPatterns.some(pattern => pattern.test(tag))
  }
  
}