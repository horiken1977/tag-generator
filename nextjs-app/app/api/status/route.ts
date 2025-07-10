import { NextResponse } from 'next/server'

export async function GET() {
  const openaiKey = process.env.OPENAI_API_KEY ? '設定済み' : '未設定'
  const claudeKey = process.env.CLAUDE_API_KEY ? '設定済み' : '未設定'
  const geminiKey = process.env.GEMINI_API_KEY ? '設定済み' : '未設定'
  
  const availableEngines = []
  if (process.env.OPENAI_API_KEY) availableEngines.push('openai')
  if (process.env.CLAUDE_API_KEY) availableEngines.push('claude')
  if (process.env.GEMINI_API_KEY) availableEngines.push('gemini')
  
  return NextResponse.json({
    status: 'running',
    timestamp: new Date().toISOString(),
    version: '3.0.0-vercel',
    platform: 'vercel',
    features: ['next-js', 'ai-integration', 'vercel-functions'],
    ai_configuration: {
      openai: openaiKey,
      claude: claudeKey,
      gemini: geminiKey,
    },
    available_engines: availableEngines,
    default_engine: availableEngines[0] || 'fallback',
    production_mode: availableEngines.length > 0
  })
}