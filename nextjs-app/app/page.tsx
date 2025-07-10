'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

interface VideoData {
  title: string
  skill: string
  description: string
  summary: string
  transcript: string
}

interface Stage1Result {
  stage: number
  success: boolean
  tag_candidates: string[]
  candidate_count: number
  processing_time: number
  message: string
}

interface Stage2Result {
  stage: number
  success: boolean
  results: Array<{
    video_index: number
    title: string
    selected_tags: string[]
    tag_count: number
    confidence: number
  }>
  statistics: {
    total_videos: number
    avg_tags_per_video: number
    total_tags_assigned: number
    processing_time: number
  }
  message: string
}

export default function Home() {
  const [currentData, setCurrentData] = useState<VideoData[]>([])
  const [stage1Results, setStage1Results] = useState<Stage1Result | null>(null)
  const [stage2Results, setStage2Results] = useState<Stage2Result | null>(null)
  const [approvedCandidates, setApprovedCandidates] = useState<string[]>([])
  const [sheetsUrl, setSheetsUrl] = useState('')
  const [aiEngine, setAiEngine] = useState('openai')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ message: '', type: 'info' })
  const [currentStage, setCurrentStage] = useState(0)
  const [systemStatus, setSystemStatus] = useState<any>(null)

  const showStatus = (message: string, type: 'info' | 'success' | 'danger' = 'info') => {
    setStatus({ message, type })
  }

  const checkSystemStatus = async () => {
    try {
      const response = await axios.get('/api/status')
      setSystemStatus(response.data)
      setAiEngine(response.data.default_engine || 'openai')
    } catch (error) {
      console.error('Status check failed:', error)
    }
  }

  // コンポーネント読み込み時にシステム状態をチェック
  useEffect(() => {
    checkSystemStatus()
  }, [])

  const loadSheetData = async () => {
    if (!sheetsUrl) {
      showStatus('Google Sheets URLを入力してください', 'danger')
      return
    }

    setLoading(true)
    showStatus('データを読み込み中...')

    try {
      const response = await axios.post('/api/sheets/data', { url: sheetsUrl })
      const result = response.data
      if (result.success) {
        setCurrentData(result.data)
        showStatus(`✅ ${result.data.length}件のデータを読み込みました`, 'success')
        setCurrentStage(1)
      } else {
        showStatus(`❌ データ読み込みエラー: ${result.error}`, 'danger')
      }
    } catch (error: any) {
      showStatus(`❌ 接続エラー: ${error.message}`, 'danger')
    } finally {
      setLoading(false)
    }
  }

  const usePreviewData = () => {
    const previewData: VideoData[] = [
      {
        title: 'マーケティング指標と財務指標を結びつけるPDCA〜財務諸表を理解する〜',
        skill: 'マーケティング',
        description: 'ROIとCPAを使った効果測定の手法',
        summary: 'Google Analyticsを活用した分析手法とPDCAサイクル',
        transcript: 'まず最初に、Google Analyticsでユーザー行動を分析します。CPAが150円、ROIが300%という結果が出ています。PDCAサイクルを使って継続的に改善していきます。'
      },
      {
        title: 'Instagram マーケティング戦略',
        skill: 'SNSマーケティング',
        description: 'Instagram を活用したブランディング手法',
        summary: 'エンゲージメント率向上とフォロワー獲得戦略',
        transcript: 'Instagramでは、ストーリーズ機能を活用することでエンゲージメント率が2.5倍向上しました。ハッシュタグ戦略も重要で、適切なタグを選ぶことでリーチが拡大します。'
      }
    ]
    setCurrentData(previewData)
    showStatus(`✅ プレビューデータ（${previewData.length}件）を読み込みました`, 'success')
    setCurrentStage(1)
  }

  const executeStage1 = async () => {
    if (!currentData.length) {
      showStatus('データを先に読み込んでください', 'danger')
      return
    }

    setLoading(true)
    showStatus('第1段階: タグ候補を生成中...')

    try {
      const response = await axios.post('/api/ai/stage1', { data: currentData })
      const result = response.data
      if (result.success) {
        setStage1Results(result)
        showStatus(`✅ ${result.candidate_count}個のタグ候補を生成しました`, 'success')
      } else {
        showStatus(`❌ 第1段階エラー: ${result.error}`, 'danger')
      }
    } catch (error: any) {
      showStatus(`❌ 接続エラー: ${error.message}`, 'danger')
    } finally {
      setLoading(false)
    }
  }

  const toggleCandidate = (candidate: string) => {
    setApprovedCandidates(prev => {
      if (prev.includes(candidate)) {
        return prev.filter(c => c !== candidate)
      } else {
        return [...prev, candidate]
      }
    })
  }

  const selectAllCandidates = () => {
    if (stage1Results) {
      setApprovedCandidates(stage1Results.tag_candidates)
    }
  }

  const deselectAllCandidates = () => {
    setApprovedCandidates([])
  }

  const approveAndProceed = () => {
    if (approvedCandidates.length === 0) {
      showStatus('少なくとも1つのタグ候補を選択してください', 'danger')
      return
    }
    setCurrentStage(2)
    showStatus(`✅ ${approvedCandidates.length}個のタグ候補を承認し、第2段階の準備が完了しました`, 'success')
  }

  const executeStage2 = async () => {
    if (!approvedCandidates.length) {
      showStatus('承認されたタグ候補がありません', 'danger')
      return
    }

    setLoading(true)
    showStatus('第2段階: 個別動画を分析中...')

    try {
      const response = await axios.post('/api/ai/stage2', {
        data: currentData,
        approved_candidates: approvedCandidates,
        ai_engine: aiEngine
      })
      const result = response.data
      if (result.success) {
        setStage2Results(result)
        showStatus(`✅ ${result.results.length}件の動画タグ付けが完了しました`, 'success')
        setCurrentStage(3)
      } else {
        showStatus(`❌ 第2段階エラー: ${result.error}`, 'danger')
      }
    } catch (error: any) {
      showStatus(`❌ 接続エラー: ${error.message}`, 'danger')
    } finally {
      setLoading(false)
    }
  }

  const exportResults = () => {
    if (!stage2Results) return

    const data = stage2Results.results.map(item => ({
      title: item.title,
      tags: item.selected_tags.join(', '),
      tag_count: item.tag_count,
      confidence: item.confidence
    }))

    const csv = [
      ['Title', 'Tags', 'Tag Count', 'Confidence'],
      ...data.map(row => [row.title, row.tags, row.tag_count, row.confidence])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `tag_results_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
  }

  const resetSystem = () => {
    setCurrentData([])
    setStage1Results(null)
    setStage2Results(null)
    setApprovedCandidates([])
    setSheetsUrl('')
    setCurrentStage(0)
    showStatus('システムがリセットされました。新しい処理を開始できます。', 'info')
  }

  return (
    <div className="container mx-auto max-w-7xl p-5">
      <div className="text-center mb-10">
        <h1 className="text-5xl font-bold mb-2 drop-shadow-lg">🏷️ Tag Generator</h1>
        <p className="text-xl">段階分離式タグ処理システム v3.0</p>
        {systemStatus && (
          <div className="mt-4 p-3 bg-white/10 rounded-lg">
            <p className="text-sm">
              🤖 AI: {systemStatus.available_engines.length > 0 ? 
                `${systemStatus.available_engines.join(', ')} 利用可能` : 
                'フォールバックモード'
              } | 
              🌐 Platform: Vercel | 
              📅 Version: {systemStatus.version}
            </p>
          </div>
        )}
      </div>

      {/* ステージインジケーター */}
      <div className="flex justify-center mb-8">
        <div className={`flex items-center px-5 py-3 mx-2 rounded-full transition-all ${
          currentStage >= 1 ? 'bg-gradient-to-r from-red-500 to-orange-500 scale-110' : 'bg-white/20'
        }`}>
          <span>📋 第1段階: タグ候補生成</span>
        </div>
        <div className={`flex items-center px-5 py-3 mx-2 rounded-full transition-all ${
          currentStage >= 2 ? 'bg-gradient-to-r from-green-500 to-teal-500 scale-110' : 'bg-white/20'
        }`}>
          <span>✅ 第2段階: 個別タグ付け</span>
        </div>
      </div>

      {/* ステータスパネル */}
      {status.message && (
        <div className={`mb-6 p-4 rounded-lg ${
          status.type === 'success' ? 'bg-green-500/30 border border-green-500/50' :
          status.type === 'danger' ? 'bg-red-500/30 border border-red-500/50' :
          'bg-blue-500/30 border border-blue-500/50'
        }`}>
          {loading ? (
            <div className="text-center">
              <div className="inline-block w-8 h-8 border-3 border-white border-t-transparent rounded-full animate-spin mb-2"></div>
              <p>{status.message}</p>
            </div>
          ) : (
            <p>{status.message}</p>
          )}
        </div>
      )}

      {/* データ入力カード */}
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 mb-6 border border-white/20">
        <h2 className="text-2xl font-bold mb-4">📊 データ入力</h2>
        <div className="space-y-4">
          <div>
            <label className="block mb-2 font-bold">Google Sheets URL:</label>
            <input
              type="url"
              value={sheetsUrl}
              onChange={(e) => setSheetsUrl(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/90 text-gray-800"
              placeholder="https://docs.google.com/spreadsheets/d/..."
            />
          </div>
          <div>
            <label className="block mb-2 font-bold">AIエンジン:</label>
            <select
              value={aiEngine}
              onChange={(e) => setAiEngine(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/90 text-gray-800"
            >
              {systemStatus?.available_engines?.includes('openai') && (
                <option value="openai">OpenAI (GPT-3.5)</option>
              )}
              {systemStatus?.available_engines?.includes('claude') && (
                <option value="claude">Claude</option>
              )}
              {systemStatus?.available_engines?.includes('gemini') && (
                <option value="gemini">Gemini</option>
              )}
              {!systemStatus?.available_engines?.length && (
                <option value="fallback">フォールバックモード（キーワード抽出）</option>
              )}
            </select>
          </div>
          <div className="flex gap-3">
            <button
              onClick={loadSheetData}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50"
            >
              📥 データ読み込み
            </button>
            <button
              onClick={usePreviewData}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50"
            >
              🔍 プレビューデータ使用
            </button>
          </div>
        </div>
      </div>

      {/* 第1段階 */}
      {currentStage >= 1 && (
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 mb-6 border border-white/20">
          <h2 className="text-2xl font-bold mb-4">📋 第1段階: タグ候補生成</h2>
          <p className="mb-4">文字起こし列を除外して全動画データを分析し、タグ候補を生成します。</p>
          <button
            onClick={executeStage1}
            disabled={loading || stage1Results !== null}
            className="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50"
          >
            🚀 タグ候補生成開始
          </button>

          {stage1Results && (
            <div className="mt-6">
              <h3 className="text-xl font-bold mb-4">🏷️ 生成されたタグ候補</h3>
              <p className="mb-4">以下のタグ候補を確認し、問題がないものにチェックを入れて承認してください：</p>
              <div className="mb-4">
                <button
                  onClick={selectAllCandidates}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg mr-2"
                >
                  ✅ 全選択
                </button>
                <button
                  onClick={deselectAllCandidates}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg"
                >
                  ❌ 全解除
                </button>
              </div>
              <div className="max-h-96 overflow-y-auto bg-white/5 rounded-lg p-4">
                {stage1Results.tag_candidates.map((candidate, index) => (
                  <div key={index} className="flex items-center p-2 bg-white/10 rounded-md mb-2">
                    <input
                      type="checkbox"
                      checked={approvedCandidates.includes(candidate)}
                      onChange={() => toggleCandidate(candidate)}
                      className="mr-3 w-5 h-5"
                    />
                    <span>{candidate}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <span>{approvedCandidates.length} / {stage1Results.tag_candidates.length} 個のタグ候補が選択されています</span>
              </div>
              <button
                onClick={approveAndProceed}
                disabled={approvedCandidates.length === 0}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50"
              >
                ✅ 承認して第2段階へ進む
              </button>
            </div>
          )}
        </div>
      )}

      {/* 第2段階 */}
      {currentStage >= 2 && (
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 mb-6 border border-white/20">
          <h2 className="text-2xl font-bold mb-4">✅ 第2段階: 個別タグ付け</h2>
          <p className="mb-4">承認されたタグ候補を使用して、文字起こしを含む各動画の詳細分析を行います。</p>
          <div className="bg-blue-500/30 border border-blue-500/50 rounded-lg p-4 mb-4">
            <strong>{approvedCandidates.length}個のタグ候補が承認されました:</strong><br />
            {approvedCandidates.slice(0, 10).join(', ')}{approvedCandidates.length > 10 ? '...' : ''}
          </div>
          <button
            onClick={executeStage2}
            disabled={loading || stage2Results !== null}
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50"
          >
            🎯 個別タグ付け開始
          </button>
        </div>
      )}

      {/* 結果表示 */}
      {stage2Results && (
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 mb-6 border border-white/20">
          <h2 className="text-2xl font-bold mb-4">🎉 タグ付け結果</h2>
          <div className="bg-green-500/30 border border-green-500/50 rounded-lg p-4 mb-4">
            <strong>📊 処理統計:</strong><br />
            総動画数: {stage2Results.statistics.total_videos}件 | 
            平均タグ数: {stage2Results.statistics.avg_tags_per_video.toFixed(1)}個/動画 | 
            総タグ数: {stage2Results.statistics.total_tags_assigned}個 | 
            処理時間: {stage2Results.statistics.processing_time.toFixed(2)}秒
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {stage2Results.results.map((item, index) => (
              <div key={index} className="bg-white/10 rounded-lg p-4">
                <div className="font-bold text-yellow-300 mb-2">{item.title.substring(0, 50)}...</div>
                <div className="text-sm text-gray-300 mb-2">
                  タグ数: {item.tag_count} | 信頼度: {(item.confidence * 100).toFixed(0)}%
                </div>
                <div className="flex flex-wrap gap-1">
                  {item.selected_tags.map((tag, tagIndex) => (
                    <span key={tagIndex} className="bg-blue-500/30 border border-blue-500/50 px-2 py-1 rounded text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button
              onClick={exportResults}
              className="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
            >
              💾 結果をダウンロード
            </button>
            <button
              onClick={resetSystem}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
            >
              🔄 新しい処理を開始
            </button>
          </div>
        </div>
      )}
    </div>
  )
}