import { NextRequest, NextResponse } from 'next/server'

// Vercelのボディサイズ制限を10MBに増加
export const runtime = 'nodejs'
export const maxDuration = 30

// CSV解析関数: ダブルクォート内の改行を適切に処理
function parseCSVLines(csvText: string): string[] {
  const lines: string[] = []
  let currentLine = ''
  let insideQuotes = false
  let i = 0
  
  while (i < csvText.length) {
    const char = csvText[i]
    const nextChar = csvText[i + 1]
    
    if (char === '"') {
      if (insideQuotes && nextChar === '"') {
        // エスケープされたクォート ("" -> ")
        currentLine += '"'
        i += 2 // 2文字分スキップ
        continue
      } else {
        // クォートの開始/終了
        insideQuotes = !insideQuotes
        currentLine += char
      }
    } else if (char === '\n' && !insideQuotes) {
      // クォート外の改行 = 行の区切り
      lines.push(currentLine)
      currentLine = ''
    } else {
      // 通常の文字またはクォート内の改行
      currentLine += char
    }
    
    i++
  }
  
  // 最後の行を追加
  if (currentLine) {
    lines.push(currentLine)
  }
  
  return lines
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, preview } = body

    // プレビューモードまたはURLが提供されていない場合
    if (!url || preview) {
      const previewData = [
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
      ]
      
      return NextResponse.json({
        success: true,
        data: previewData,
        total_rows: previewData.length, // 実際のデータ数に基づく
        processed_rows: previewData.length
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
    
    // 適切なCSV解析: ダブルクォート内の改行を考慮
    const csvLines = parseCSVLines(normalizedText.trim())
    
    console.log(`Properly parsed CSV lines: ${csvLines.length}`)
    console.log(`First 3 lines:`, csvLines.slice(0, 3))
    
    if (csvLines.length < 2) {
      return NextResponse.json({
        success: false,
        error: 'スプレッドシートが空か、データが不十分です'
      }, { status: 400 })
    }

    // CSVをパース
    const headers = csvLines[0].split(',').map(h => h.trim().replace(/"/g, ''))
    console.log(`Headers detected:`, headers)
    
    const data = []

    // デバッグ情報を追加
    console.log(`CSVパース: ${csvLines.length}行を検出`)

    // 厳格な行数制限（400行程度を想定）
    const maxRows = Math.min(csvLines.length, 500)
    console.log(`Processing maximum ${maxRows} rows (limited for safety)`)
    
    if (csvLines.length > 500) {
      console.log(`⚠️ WARNING: CSV has ${csvLines.length} lines, limiting to first 500 rows`)
    }

    for (let i = 1; i < maxRows; i++) {
      // 空行をスキップ
      if (!csvLines[i].trim()) continue
      
      // CSVの行をより正確にパース
      const values = []
      let current = ''
      let inQuotes = false
      
      for (let j = 0; j < csvLines[i].length; j++) {
        const char = csvLines[i][j]
        const nextChar = csvLines[i][j + 1]
        
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
      if (row.title && row.title.trim() && row.title.length > 3) {
        // タイトルが短すぎるものや無意味なものを除外
        if (!/^[\s\-_,\.]*$/.test(row.title)) {
          row.skill = row.skill || 'ビジネススキル'
          row.description = row.description || row.title
          row.summary = row.summary || row.title
          row.transcript = ''
          data.push(row)
        }
      }
    }
    
    console.log(`処理済み: ${data.length}件のデータ`)
    
    // 最終的なデータ数制限（400件程度を想定）
    if (data.length > 450) {
      console.log(`⚠️ データが多すぎます (${data.length}件) - 最初の450件に制限`)
      data.splice(450)
    }
    
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
        csv_lines: csvLines.length,
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