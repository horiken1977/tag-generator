import { NextRequest, NextResponse } from 'next/server'

// Vercelのボディサイズ制限を10MBに増加
export const runtime = 'nodejs'
export const maxDuration = 30

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, preview } = body

    // プレビューモードまたはURLが提供されていない場合
    if (!url || preview) {
      return NextResponse.json({
        success: true,
        data: [
          {
            title: '効果的なプレゼンテーション技法',
            skill: 'コミュニケーション',
            description: '聴衆を惹きつけるプレゼンテーション技法を学ぶ',
            summary: 'プレゼンテーションの基本構成と効果的な伝達方法',
            transcript: 'プレゼンテーションにおいて最も重要なのは...'
          },
          {
            title: 'デジタルマーケティング基礎',
            skill: 'マーケティング',
            description: 'SEOとSNS活用による効果的なデジタルマーケティング戦略',
            summary: 'デジタル時代のマーケティング手法と実践方法',
            transcript: 'デジタルマーケティングの核心は顧客との接点を...'
          }
        ],
        total_rows: 400,
        processed_rows: 2
      })
    }

    // Google SheetsのIDを抽出
    const sheetIdMatch = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/)
    if (!sheetIdMatch) {
      return NextResponse.json({
        success: false,
        error: 'Google Sheets URLからIDを抽出できません'
      }, { status: 400 })
    }

    const sheetId = sheetIdMatch[1]
    const csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=0`

    // CSVデータを取得
    const response = await fetch(csvUrl, {
      headers: { 'User-Agent': 'TagGenerator/3.0' }
    })

    if (!response.ok) {
      if (response.status === 403) {
        return NextResponse.json({
          success: false,
          error: 'アクセスが拒否されました。スプレッドシートを公開設定にしてください。'
        }, { status: 403 })
      }
      return NextResponse.json({
        success: false,
        error: `HTTP ${response.status}: スプレッドシートにアクセスできません`
      }, { status: response.status })
    }

    const csvText = await response.text()
    
    // 詳細なデバッグ情報
    console.log('=== CSV DEBUG INFO ===')
    console.log(`Raw CSV length: ${csvText.length} characters`)
    console.log(`First 500 chars: ${csvText.slice(0, 500)}`)
    console.log(`Contains \\r: ${csvText.includes('\r')}`)
    console.log(`Contains \\n: ${csvText.includes('\n')}`)
    console.log(`Contains \\r\\n: ${csvText.includes('\r\n')}`)
    
    // 改行の正規化（CR、LF、CRLFに対応）
    const normalizedText = csvText.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const lines = normalizedText.trim().split('\n').filter(line => line.trim() !== '')
    
    console.log(`Lines after split: ${lines.length}`)
    console.log(`First 5 lines:`, lines.slice(0, 5))
    
    if (lines.length < 2) {
      return NextResponse.json({
        success: false,
        error: 'スプレッドシートが空か、データが不十分です'
      }, { status: 400 })
    }

    // CSVをパース
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
    console.log(`Headers detected:`, headers)
    
    const data = []

    // デバッグ情報を追加
    console.log(`CSVパース: ${lines.length}行を検出`)

    // 安全のため最大5000行に制限
    const maxRows = Math.min(lines.length, 5000)
    console.log(`Processing maximum ${maxRows} rows`)

    for (let i = 1; i < maxRows; i++) {
      // 空行をスキップ
      if (!lines[i].trim()) continue
      
      // CSVの行をより正確にパース
      const values = []
      let current = ''
      let inQuotes = false
      
      for (let j = 0; j < lines[i].length; j++) {
        const char = lines[i][j]
        const nextChar = lines[i][j + 1]
        
        if (char === '"' && nextChar === '"') {
          current += '"'
          j++ // スキップ
        } else if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          values.push(current)
          current = ''
        } else {
          current += char
        }
      }
      values.push(current) // 最後の値を追加
      
      const row: any = {}
      
      values.forEach((value, index) => {
        const cleanValue = value.trim().replace(/^"|"$/g, '')
        const header = headers[index]?.toLowerCase() || ''
        
        // 列名のマッピング
        if (header.includes('title') || header.includes('タイトル')) {
          row.title = cleanValue.slice(0, 100) // 文字数制限
        } else if (header.includes('skill') || header.includes('スキル')) {
          row.skill = cleanValue.slice(0, 50)
        } else if (header.includes('description') || header.includes('説明')) {
          row.description = cleanValue.slice(0, 200)
        } else if (header.includes('summary') || header.includes('要約')) {
          row.summary = cleanValue.slice(0, 200)
        } else if (header.includes('transcript') || header.includes('文字起こし')) {
          // 文字起こしは保存しない
          row.transcript = ''
        }
      })

      // 必須フィールドの確認とデフォルト値設定
      if (row.title && row.title.trim()) {
        row.skill = row.skill || 'ビジネススキル'
        row.description = row.description || row.title
        row.summary = row.summary || row.title
        row.transcript = ''
        data.push(row)
      }
    }
    
    console.log(`処理済み: ${data.length}件のデータ`)
    
    // JSONサイズの確認
    const jsonString = JSON.stringify(data)
    console.log(`JSON size: ${jsonString.length} characters`)
    console.log(`JSON size: ${(jsonString.length / 1024 / 1024).toFixed(2)} MB`)

    return NextResponse.json({
      success: true,
      data: data,
      total_rows: data.length,
      processed_rows: data.length,
      source: 'google_sheets',
      sheet_id: sheetId,
      debug_info: {
        csv_lines: lines.length,
        processed_data: data.length,
        json_size_mb: (jsonString.length / 1024 / 1024).toFixed(2)
      }
    })

  } catch (error: any) {
    console.error('Sheets API error:', error)
    return NextResponse.json({
      success: false,
      error: `データ読み込みエラー: ${error.message}`
    }, { status: 500 })
  }
}