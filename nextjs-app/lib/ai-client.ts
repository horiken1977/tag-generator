// AI API client for tag generation

interface AIResponse {
  success: boolean
  tags?: string[]
  error?: string
}

export class AIClient {
  private baseUrl = 'https://api.openai.com/v1/chat/completions'
  
  async generateTags(content: string, engine: string = 'openai'): Promise<string[]> {
    try {
      if (engine === 'openai') {
        return await this.callOpenAI(content)
      } else if (engine === 'claude') {
        return await this.callClaude(content)
      } else if (engine === 'gemini') {
        return await this.callGemini(content)
      }
      
      // Fallback to keyword extraction
      return this.extractKeywords(content)
    } catch (error) {
      console.error('AI API error:', error)
      return this.extractKeywords(content)
    }
  }
  
  private async callOpenAI(content: string): Promise<string[]> {
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      throw new Error('OpenAI API key not configured')
    }
    
    const prompt = this.buildPrompt(content)
    
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
        max_tokens: 500,
        temperature: 0.3
      })
    })
    
    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status}`)
    }
    
    const data = await response.json()
    const result = data.choices[0]?.message?.content || ''
    
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
        max_tokens: 500,
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
    
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`, {
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
          maxOutputTokens: 500
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
以下のマーケティング動画データを分析して、具体的で検索に有用なタグを10-15個生成してください。

【コンテンツ】:
${content.substring(0, 2000)}

【タグ生成の基準】:
1. 具体的なツール名・サービス名・手法名
2. 業界固有の概念・理論・フレームワーク  
3. 測定可能な指標名・KPI
4. 具体的なプロセス名・手順名
5. 職種・業界・分野名

【絶対に避けるべき汎用語】:
- 「6つの要素」「8つの分類」「4つのポイント」等の数字+汎用語
- 「要素」「分類」「ポイント」「手法」「方法」「技術」等の単体使用
- 「基本」「応用」「実践」「理論」「概要」「入門」等の抽象表現

出力: 具体的で有用なタグのみをカンマ区切りで出力してください。
`
  }
  
  private parseTagsFromResponse(response: string): string[] {
    // Extract tags from AI response
    const tags = response
      .split(/[,\n]/)
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0 && tag.length < 50)
      .filter(tag => !this.isGenericTag(tag))
      .slice(0, 15)
    
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
  
  private extractKeywords(content: string): string[] {
    // Fallback keyword extraction
    const keywords: string[] = []
    
    // Extract English words
    const englishWords = content.match(/[A-Z][a-zA-Z]+/g) || []
    keywords.push(...englishWords.filter(w => w.length >= 3))
    
    // Extract katakana words
    const katakanaWords = content.match(/[ァ-ヶー]+/g) || []
    keywords.push(...katakanaWords.filter(w => w.length >= 3))
    
    // Extract important keywords
    const importantKeywords = [
      'Google Analytics', 'ROI', 'CPA', 'Instagram', 'Facebook', 
      'SEO', 'SEM', 'KPI', 'OKR', 'エンゲージメント率'
    ]
    
    importantKeywords.forEach(keyword => {
      if (content.includes(keyword)) {
        keywords.push(keyword)
      }
    })
    
    return [...new Set(keywords)].slice(0, 15)
  }
}