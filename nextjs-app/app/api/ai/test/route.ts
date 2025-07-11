import { NextRequest, NextResponse } from 'next/server'
import { AIClient } from '@/lib/ai-client'

// Vercelのボディサイズ制限とタイムアウト設定
export const runtime = 'nodejs'
export const maxDuration = 30

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const aiEngine = body.engine || 'openai'
    
    console.log(`🧪 AI接続テスト開始: ${aiEngine}`)
    
    // 簡単なテストテキスト
    const testText = "マーケティング分析とデータドリブンな意思決定について学ぶ動画です。Google AnalyticsやROI測定の基本を説明します。"
    
    const startTime = Date.now()
    
    try {
      const aiClient = new AIClient()
      const result = await aiClient.generateTags(testText, aiEngine)
      
      const processingTime = Date.now() - startTime
      
      console.log(`✅ AI接続テスト成功: ${aiEngine}, 処理時間: ${processingTime}ms, 結果: ${result.length}個のタグ`)
      
      return NextResponse.json({
        success: true,
        engine: aiEngine,
        processing_time: processingTime,
        tags_generated: result.length,
        sample_tags: result.slice(0, 3),
        message: `${aiEngine}との接続に成功しました (${processingTime}ms)`
      })
      
    } catch (error: any) {
      const processingTime = Date.now() - startTime
      
      console.error(`❌ AI接続テスト失敗: ${aiEngine}, エラー:`, error)
      
      return NextResponse.json({
        success: false,
        engine: aiEngine,
        processing_time: processingTime,
        error: error.message,
        message: `${aiEngine}との接続に失敗しました: ${error.message}`
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