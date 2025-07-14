import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 30

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const preferredEngine = body.engine || 'openai'
    
    console.log(`🧪 AI接続テスト開始: ${preferredEngine}`)
    
    // 簡単なテストテキスト
    const testText = "マーケティング分析とデータドリブンな意思決定について学ぶ動画です。Google AnalyticsやROI測定の基本を説明します。"
    
    // API環境変数チェック
    const hasOpenAI = !!process.env.OPENAI_API_KEY
    const hasClaude = !!process.env.CLAUDE_API_KEY
    const hasGemini = !!process.env.GEMINI_API_KEY
    
    // ユーザー指定エンジンを優先し、フォールバック用の他のエンジンも準備
    let engines: string[] = []
    
    if (preferredEngine && ((preferredEngine === 'openai' && hasOpenAI) || 
                            (preferredEngine === 'claude' && hasClaude) || 
                            (preferredEngine === 'gemini' && hasGemini))) {
      engines.push(preferredEngine)
      // フォールバック用に他のエンジンも追加（優先度順）
      if (preferredEngine !== 'claude' && hasClaude) engines.push('claude')
      if (preferredEngine !== 'gemini' && hasGemini) engines.push('gemini') 
      if (preferredEngine !== 'openai' && hasOpenAI) engines.push('openai')
    } else {
      // 従来の優先順位: Claude > Gemini > OpenAI
      engines = [
        ...(hasClaude ? ['claude'] : []),
        ...(hasGemini ? ['gemini'] : []),
        ...(hasOpenAI ? ['openai'] : [])
      ]
    }
    
    const startTime = Date.now()
    const aiClient = new AIClient()
    
    let result: string[] = []
    let lastError: any = null
    let successEngine: string = ''
    
    // フォールバック機能付きでAI呼び出し
    for (const engine of engines) {
      try {
        console.log(`🔄 ${engine}で接続テストを試行中...${engine === preferredEngine ? ' (ユーザー選択)' : ' (フォールバック)'}`)
        result = await aiClient.generateTags(testText, engine)
        successEngine = engine
        console.log(`✅ ${engine}で成功: ${result.length}個のタグ`)
        break
      } catch (error: any) {
        lastError = error
        console.log(`❌ ${engine}で失敗: ${error.message}`)
        
        // OpenAIのクォータエラーは予想されるので詳細ログを出力しない
        if (engine === 'openai' && error.message.includes('quota')) {
          console.log(`⚠️  OpenAI quota exceeded, falling back to other engines`)
        }
        
        // 最後のエンジンでなければ続行
        if (engine !== engines[engines.length - 1]) {
          console.log(`🔄 次のエンジンにフォールバック...`)
          continue
        }
      }
    }
    
    const processingTime = Date.now() - startTime
    
    if (result.length > 0 && successEngine) {
      console.log(`✅ AI接続テスト成功: ${successEngine}, 処理時間: ${processingTime}ms, 結果: ${result.length}個のタグ`)
      
      return NextResponse.json({
        success: true,
        engine: successEngine,
        requested_engine: preferredEngine,
        processing_time: processingTime,
        tags_generated: result.length,
        sample_tags: result.slice(0, 3),
        message: successEngine === preferredEngine 
          ? `${successEngine}との接続に成功しました (${processingTime}ms)`
          : `${preferredEngine}は利用できませんでしたが、${successEngine}での接続に成功しました (${processingTime}ms)`
      })
    } else {
      const processingTime = Date.now() - startTime
      
      console.error(`❌ AI接続テスト失敗: 全てのエンジンで失敗`)
      console.error(`エラー詳細:`, {
        message: lastError?.message || 'Unknown error',
        stack: lastError?.stack,
        name: lastError?.name,
        cause: lastError?.cause
      })
      
      console.log(`🔑 API keys status: OpenAI=${hasOpenAI}, Claude=${hasClaude}, Gemini=${hasGemini}`)
      console.log(`🔍 試行したエンジン: ${engines.join(', ')}`)
      
      return NextResponse.json({
        success: false,
        engine: preferredEngine,
        tried_engines: engines,
        processing_time: processingTime,
        error: lastError?.message || 'All AI engines failed',
        error_details: {
          name: lastError?.name || 'Error',
          message: lastError?.message || 'All AI engines failed',
          has_openai_key: hasOpenAI,
          has_claude_key: hasClaude,
          has_gemini_key: hasGemini
        },
        message: `全てのAIエンジンで接続に失敗しました: ${lastError?.message || 'Unknown error'}`
      }, { status: 400 })
    }
    
  } catch (error: any) {
    console.error('AI接続テストエラー:', error)
    return NextResponse.json({
      success: false,
      error: `テストリクエストエラー: ${error.message}`
    }, { status: 500 })
  }
}