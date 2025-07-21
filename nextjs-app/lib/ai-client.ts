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

  // Stage2: 個別動画タグ選択（文字起こし含む5列分析）
  async selectTagsForVideo(videoContent: string, tagCandidates: string[], engine: string = 'openai'): Promise<string[]> {
    const candidatesString = tagCandidates.join(', ')
    
    let aiGeneratedTags: string[] = []
    
    if (engine === 'openai') {
      aiGeneratedTags = await this.callOpenAI(`${videoContent}|||${candidatesString}`, 'select')
    } else if (engine === 'claude') {
      aiGeneratedTags = await this.callClaude(`${videoContent}|||${candidatesString}`, 'select')
    } else if (engine === 'gemini') {
      aiGeneratedTags = await this.callGemini(`${videoContent}|||${candidatesString}`, 'select')
    } else {
      throw new Error(`Unsupported AI engine: ${engine}`)
    }
    
    // 厳格なタグ検証: Stage1候補からのみ選択
    const validatedTags = this.validateTagsAgainstCandidates(aiGeneratedTags, tagCandidates)
    console.log(`🔍 タグ検証: AI生成${aiGeneratedTags.length}個 → 有効${validatedTags.length}個`)
    
    return validatedTags
  }
  
  private async callOpenAI(content: string, promptType: 'standard' | 'light' | 'optimize' | 'select' = 'standard'): Promise<string[]> {
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      throw new Error('OpenAI API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else if (promptType === 'select') {
      const [videoContent, candidates] = content.split('|||')
      prompt = this.buildSelectPrompt(videoContent, candidates.split(',').map(c => c.trim()))
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
    
    // Stage2の場合は専用の解析を使用
    return promptType === 'select' 
      ? this.parseSelectedTagsFromResponse(result)
      : this.parseTagsFromResponse(result)
  }
  
  private async callClaude(content: string, promptType: 'standard' | 'light' | 'optimize' | 'select' = 'standard'): Promise<string[]> {
    const apiKey = process.env.CLAUDE_API_KEY
    if (!apiKey) {
      throw new Error('Claude API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else if (promptType === 'select') {
      const [videoContent, candidates] = content.split('|||')
      prompt = this.buildSelectPrompt(videoContent, candidates.split(',').map(c => c.trim()))
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
    
    // Stage2の場合は専用の解析を使用
    const tags = promptType === 'select' 
      ? this.parseSelectedTagsFromResponse(result)
      : this.parseTagsFromResponse(result)
    
    // デバッグ用：parseTagsFromResponseの前後を確認
    if (tags.length === 0 && result.length > 0) {
      console.log(`⚠️ Claude応答はあったが、タグが0個になりました。応答内容: "${result}"`)
    }
    
    return tags
  }
  
  private async callGemini(content: string, promptType: 'standard' | 'light' | 'optimize' | 'select' = 'standard'): Promise<string[]> {
    const apiKey = process.env.GEMINI_API_KEY
    if (!apiKey) {
      throw new Error('Gemini API key not configured')
    }
    
    let prompt: string
    if (promptType === 'light') {
      prompt = this.buildLightPrompt(content)
    } else if (promptType === 'optimize') {
      prompt = this.buildOptimizePrompt(content.split(',').map(k => k.trim()))
    } else if (promptType === 'select') {
      const [videoContent, candidates] = content.split('|||')
      prompt = this.buildSelectPrompt(videoContent, candidates.split(',').map(c => c.trim()))
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
    
    // Stage2の場合は専用の解析を使用
    return promptType === 'select' 
      ? this.parseSelectedTagsFromResponse(result)
      : this.parseTagsFromResponse(result)
  }
  
  private buildPrompt(content: string): string {
    return `
以下は400-450件のマーケティング動画データの統合分析です。このデータ全体を深く分析して、具体的で検索に有用なタグを250-300個生成してください。

【全動画データ】:
${content}

【重要な指示】:
- 400-450件の動画データ全体を分析対象とする
- 多様性を重視し、異なる分野・手法・ツールから幅広くタグを抽出
- 250-300個の豊富なタグ候補を生成する（最低250個、理想300個）

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

【重要な出力要件】: 8000個以上のキーワードから僅か100個程度は絶対に不十分です。必ず250個以上、理想的には300個のタグを生成してください。

出力形式: 具体的で有用なタグのみをカンマ区切りで300個出力してください。1行ずつではなく、カンマ区切りで連続して出力してください。250個未満は不合格です。
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

【品質重視の抽出ルール】:
1. 名詞形で抽出（動詞は名詞化: 「分析する」→「分析」）
2. 一般的に理解できる用語を優先
3. 検索価値のある具体的な語のみ
4. 専門用語は略語と正式名称両方を含める

【避けるべき語】:
- 助詞・接続詞・一般的すぎる語（「する」「ある」「方法」「技術」等の単体使用）
- 「6つの」「8つの」等の数量表現のみ  
- 抽象的すぎる語（「成長」「理解」「知る」「分かる」「迷子」等）
- 特殊用語（「ステージ1」「フェーズ2」「レイヤー」等）

【重要な出力形式】:
検索に有用で具体的なキーワードを20-30個、必ずカンマ区切りで1行に出力してください。
例: キーワード1, キーワード2, キーワード3, キーワード4, ...

【禁止事項】:
- 改行での区切り
- 番号付きリスト
- 説明文の追加
- 「以下のキーワードを抽出しました」等の前置き

出力: (キーワードのみをカンマ区切りで)
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
以下は450件のマーケティング動画から抽出された${keywords.length}個のキーワードです。これらを統合・整理して、重複を排除し、最も重要で検索に有用な300個のタグを生成してください。

【収集されたキーワード】:
${keywordText}

【統合・最適化の指示】:
1. 同じ概念の異なる表現を統合（例：「デジタルマーケティング」「オンラインマーケティング」→「デジタルマーケティング」）
2. 重要度と出現頻度を考慮した優先順位付け
3. 全体のバランスを取り、多様な分野をカバー
4. 具体性と検索有用性を重視
5. 豊富な選択肢を提供するため、質の高いタグを可能な限り多く抽出

【品質向上の重要ルール】:
1. 名詞形で統一（動詞は名詞化: 「分析する」→「分析」、「企画する」→「企画」）
2. 一般的に理解できる用語を優先（「ステージ1」→「初級レベル」、「フェーズ2」→「中級段階」）
3. 類似語の完全統合（「マーケティング」「マーケ」→「マーケティング」）
4. 検索価値のない抽象語を除外（「成長」「理解」「知る」「分かる」等）
5. 専門用語は一般的な表現に変換（「ROI」→「投資回収率」、「CTR」→「クリック率」）

【出力要求】:
- 300個の高品質タグ（絶対最低250個、目標300個）
- 重複・類似語なし
- 名詞形で統一
- 一般的に理解可能
- 検索に実用的
- カンマ区切りで出力

【重要】: ${keywords.length}個のキーワードから僅か100個程度のタグしか生成しないのは不十分です。豊富な選択肢を提供するため、必ず250個以上、理想的には300個のタグを生成してください。

出力: 最適化された300個のタグをカンマ区切りで出力してください。250個未満は不合格です。
`
  }

  // Stage2: 個別動画タグ選択用プロンプト
  private buildSelectPrompt(videoContent: string, tagCandidates: string[]): string {
    return `
以下の動画について、承認されたタグ候補から最も適切なタグを15個選択してください。

【動画データ】:
${videoContent}

【承認済みタグ候補（${tagCandidates.length}個）】:
${tagCandidates.join(', ')}

【選定基準（優先順位順）】:
🎯 **最優先: 差別化と特異性**
1. この動画でしか言及されない具体的なツール名・サービス名・手法名
2. 文字起こしに登場する固有名詞・数値・具体的事例
3. 他の類似動画では扱われない専門的な概念・理論

🔍 **第2優先: 文字起こし直接関連性**
4. 文字起こしで複数回言及される重要キーワード
5. 動画の核心内容を表す専門用語

⚡ **第3優先: 実用性と検索価値**
6. 検索時に有用で具体性の高いタグ
7. 学習者が求める実践的な知識を表すタグ

【絶対に避けるべき汎用タグ（具体例）】:
❌ 「ビジネススキル」「マーケティング」「営業」「コミュニケーション」
❌ 「プレゼンテーション」「リーダーシップ」「マネジメント」「戦略」
❌ 「分析」「改善」「効率化」「最適化」「向上」「強化」
❌ 「基本」「応用」「実践」「理論」「入門」「概要」
❌ 「スキル開発」「人材育成」「業務改善」「組織運営」

【良いタグの具体例】:
✅ 「Google Analytics 4」「Salesforce CRM」「Instagram広告」
✅ 「ROI計算」「A/Bテスト」「コンバージョン率」「LTV分析」
✅ 「PDCA サイクル」「OKR設定」「KPI設計」「SWOT分析」
✅ 「Excel関数」「Power BI」「Tableau」「SQL クエリ」

【厳守事項】:
- 新しいタグは作成せず、承認済み候補からのみ選択
- 文字起こしに全く関連しないタグは絶対に選択しない
- 汎用的すぎるタグは差別化の観点から除外
- 必ず15個のタグを選択（12-18個の範囲で調整可能）

【出力形式】:
選択したタグのみを必ずカンマ区切りで1行に出力してください。
例: タグ1, タグ2, タグ3, タグ4, タグ5

【絶対禁止】:
- 改行、番号付きリスト、箇条書きは禁止
- 説明文、前置き、理由は一切不要
- タグ名のみをカンマとスペースで区切る
- 「以下のタグを選択しました」等の文言は不要

出力: 
`
  }
  
  private parseTagsFromResponse(response: string): string[] {
    console.log(`🔍 原文応答（最初の500文字）: "${response.substring(0, 500)}"`)
    
    // より柔軟な分割パターンを試行
    let splitTags: string[] = []
    
    // パターン1: カンマ区切り
    if (response.includes(',')) {
      splitTags = response.split(/[,，]/)
      console.log(`📝 カンマ区切りで分割: ${splitTags.length}個`)
    }
    // パターン2: 改行区切り
    else if (response.includes('\n')) {
      splitTags = response.split(/\r?\n/)
      console.log(`📝 改行区切りで分割: ${splitTags.length}個`)
    }
    // パターン3: スペース区切り（最後の手段）
    else {
      splitTags = response.split(/\s+/)
      console.log(`📝 スペース区切りで分割: ${splitTags.length}個`)
    }
    
    const trimmedTags = splitTags.map(tag => tag.trim())
    const nonEmptyTags = trimmedTags.filter(tag => tag.length > 0)
    let filteredTags = nonEmptyTags.filter(tag => !this.isGenericTag(tag))
    
    // フィルター後のタグ数が200個未満の場合は警告してフィルターを緩める
    if (filteredTags.length < 200) {
      console.log(`⚠️ フィルター後のタグ数が少なすぎます (${filteredTags.length}個)。フィルターを緩めて元のタグを使用します。`)
      // 最低限のフィルターのみ適用（極端に短いタグと明らかに無意味なもののみ除外）
      filteredTags = nonEmptyTags.filter(tag => 
        tag.length >= 2 && 
        !tag.match(/^[。、.,\s]*$/) &&
        !tag.match(/^する$/) &&
        !tag.match(/^なる$/) &&
        !tag.match(/^いる$/)
      )
      console.log(`🔧 緩いフィルター適用後: ${filteredTags.length}個`)
    }
    
    const finalTags = filteredTags.slice(0, 300) // 最大300個に制限
    
    console.log(`🏷️ タグ解析詳細: 分割=${splitTags.length}, 空除去=${nonEmptyTags.length}, 汎用語除去=${filteredTags.length}, 最終=${finalTags.length}`)
    
    // デバッグ：最初の10個のタグを表示
    console.log(`📋 最初の10個のタグ: ${finalTags.slice(0, 10).join(', ')}`)
    
    // デバッグ：汎用語としてフィルタされたタグを表示
    if (nonEmptyTags.length > filteredTags.length) {
      const genericTags = nonEmptyTags.filter(tag => this.isGenericTag(tag))
      console.log(`🚫 汎用語として除外されたタグ: ${genericTags.slice(0, 10).join(', ')}${genericTags.length > 10 ? ` (他${genericTags.length - 10}個)` : ''}`)
    }
    
    // 最終タグ数の品質チェック
    if (finalTags.length < 200) {
      console.log(`⚠️ 最終タグ数が目標を下回っています: ${finalTags.length}個 (目標: 200個以上)`)
    } else {
      console.log(`✅ 十分なタグ数を確保: ${finalTags.length}個`)
    }
    
    return finalTags
  }

  // Stage2専用: 選択されたタグの解析（より厳密な処理）
  private parseSelectedTagsFromResponse(response: string): string[] {
    console.log(`🔍 Stage2応答（全文）: "${response}"`)
    
    // 不要な前置きや説明文を除去
    let cleanResponse = response
      .replace(/^(以下|選択した|抽出した|おすすめの|関連する).*?[：:]/g, '')
      .replace(/^.*?(タグ|キーワード).*?[：:]/g, '')
      .replace(/^.*?結果.*?[：:]/g, '')
      .trim()
    
    console.log(`🧹 クリーンアップ後: "${cleanResponse}"`)
    
    // より柔軟な分割パターンを試行（Stage2専用）
    let splitTags: string[] = []
    
    // パターン1: カンマ区切り（最優先）
    if (cleanResponse.includes(',')) {
      splitTags = cleanResponse.split(/[,，、]/)
      console.log(`📝 カンマ区切りで分割: ${splitTags.length}個`)
    }
    // パターン2: 改行区切り
    else if (cleanResponse.includes('\n')) {
      splitTags = cleanResponse.split(/\r?\n/)
      console.log(`📝 改行区切りで分割: ${splitTags.length}個`)
    }
    // パターン3: 番号付きリスト（1. 2. 3.）
    else if (/\d+\./.test(cleanResponse)) {
      splitTags = cleanResponse.split(/\d+\./).filter(tag => tag.trim().length > 0)
      console.log(`📝 番号付きリストで分割: ${splitTags.length}個`)
    }
    // パターン4: 箇条書き（- * •）
    else if (/[-\*•]/.test(cleanResponse)) {
      splitTags = cleanResponse.split(/[-\*•]/).filter(tag => tag.trim().length > 0)
      console.log(`📝 箇条書きで分割: ${splitTags.length}個`)
    }
    // パターン5: スペース区切り（最後の手段）
    else {
      splitTags = cleanResponse.split(/\s+/)
      console.log(`📝 スペース区切りで分割: ${splitTags.length}個`)
    }
    
    const trimmedTags = splitTags.map(tag => tag.trim())
    const nonEmptyTags = trimmedTags.filter(tag => tag.length > 0)
    // Stage2では汎用語フィルタを緩くする（既に選択されたタグなので）
    const filteredTags = nonEmptyTags.filter(tag => tag.length > 1 && !tag.match(/^[。、.,\s]*$/))
    const finalTags = filteredTags.slice(0, 15) // Stage2は最大15個
    
    console.log(`🏷️ Stage2タグ解析: 分割=${splitTags.length}, 空除去=${nonEmptyTags.length}, フィルタ後=${filteredTags.length}, 最終=${finalTags.length}`)
    console.log(`📋 選択されたタグ: ${finalTags.join(', ')}`)
    
    return finalTags
  }
  
  private isGenericTag(tag: string): boolean {
    const genericPatterns = [
      // 数字+汎用語のパターン
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
      /^入門$/,
      // 抽象的すぎる語（品質向上のため追加）
      /^理解$/,
      /^知る$/,
      /^分かる$/,
      /^迷子$/,
      // 特殊用語パターン
      /^ステージ\d+$/,
      /^フェーズ\d+$/,
      /^レイヤー$/,
      /^段階$/,
      // 動詞形（名詞化されていない）
      /する$/,
      /なる$/,
      /である$/,
      /いる$/
    ]
    
    return genericPatterns.some(pattern => pattern.test(tag))
  }

  private validateTagsAgainstCandidates(aiTags: string[], tagCandidates: string[]): string[] {
    console.log(`🔍 タグ候補検証開始: AI生成${aiTags.length}個を検証`)
    
    // 承認済み候補をセットに変換（高速検索のため）
    const approvedSet = new Set(tagCandidates)
    
    const validatedTags: string[] = []
    const invalidTags: string[] = []
    
    for (const tag of aiTags) {
      // 前後の空白を除去し、改行等の制御文字を除去
      let cleanedTag = tag.trim().replace(/\n/g, '').replace(/\r/g, '')
      
      // プロンプトの応答形式問題を修正（「以下のタグを選択しました」等の除去）
      if (cleanedTag.startsWith('以下の') || cleanedTag.startsWith('選択した') || cleanedTag.includes('選択しました')) {
        continue
      }
      
      // 空のタグや短すぎるタグをスキップ
      if (!cleanedTag || cleanedTag.length < 2) {
        continue
      }
      
      // Stage1候補との完全一致チェック
      if (approvedSet.has(cleanedTag)) {
        if (!validatedTags.includes(cleanedTag)) { // 重複排除
          validatedTags.push(cleanedTag)
        }
      } else {
        // 部分一致チェック（類似タグの救済）
        const partialMatch = this.findPartialMatch(cleanedTag, tagCandidates)
        if (partialMatch) {
          if (!validatedTags.includes(partialMatch)) {
            validatedTags.push(partialMatch)
            console.log(`    部分一致救済: '${cleanedTag}' → '${partialMatch}'`)
          }
        } else {
          invalidTags.push(cleanedTag)
        }
      }
    }
    
    // 検証結果のログ出力
    console.log(`  検証結果: ${validatedTags.length}個有効、${invalidTags.length}個無効`)
    if (invalidTags.length > 0) {
      console.log(`  無効タグ例: ${invalidTags.slice(0, 5).join(', ')}${invalidTags.length > 5 ? '...' : ''}`)
    }
    
    // 15個に満たない場合のフォールバック処理
    if (validatedTags.length < 15) {
      const shortage = 15 - validatedTags.length
      const remainingCandidates = tagCandidates.filter(c => !validatedTags.includes(c))
      
      if (remainingCandidates.length > 0) {
        // リストの最初から追加（一貫性のため）
        const additionalTags = remainingCandidates.slice(0, shortage)
        validatedTags.push(...additionalTags)
        console.log(`  フォールバック: ${additionalTags.length}個のタグを追加して15個に調整`)
      }
    }
    
    return validatedTags.slice(0, 15) // 厳格に15個まで
  }

  private findPartialMatch(tag: string, candidates: string[]): string | null {
    const tagLower = tag.toLowerCase()
    
    // 完全一致（大小文字無視）
    for (const candidate of candidates) {
      if (tagLower === candidate.toLowerCase()) {
        return candidate
      }
    }
    
    // 包含関係での一致（短いタグが長いタグに含まれる場合）
    for (const candidate of candidates) {
      if (tagLower.includes(candidate.toLowerCase()) || candidate.toLowerCase().includes(tagLower)) {
        // ただし、長さの差が大きすぎる場合は除外
        if (Math.abs(tag.length - candidate.length) <= 3) {
          return candidate
        }
      }
    }
    
    return null
  }
  
}