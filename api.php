<?php
/**
 * Tag Generator API エンドポイント
 * personaagentの構成を参考にしたPHP版API
 */

// エラー報告設定
error_reporting(E_ALL);
ini_set('display_errors', 0);

// タイムゾーン設定
date_default_timezone_set('Asia/Tokyo');

// CORS設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json; charset=utf-8');

// プリフライトリクエストの処理
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// .envファイルの読み込み
function loadEnv() {
    $envVars = [];
    if (file_exists(__DIR__ . '/.env')) {
        $envLines = file(__DIR__ . '/.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($envLines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                $envVars[trim($key)] = trim($value);
            }
        }
    }
    return $envVars;
}

// APIキー取得
function getApiKey($provider) {
    static $envVars = null;
    if ($envVars === null) {
        $envVars = loadEnv();
    }
    
    $keyMap = [
        'openai' => 'OPENAI_API_KEY',
        'claude' => 'CLAUDE_API_KEY',
        'gemini' => 'GEMINI_API_KEY'
    ];
    
    return $envVars[$keyMap[$provider]] ?? '';
}

// JSON レスポンス送信
function sendJsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Google Sheets CSV データ取得
function fetchGoogleSheetsData($url) {
    // スプレッドシートIDを抽出
    if (preg_match('/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/', $url, $matches)) {
        $sheetId = $matches[1];
        $csvUrl = "https://docs.google.com/spreadsheets/d/{$sheetId}/export?format=csv&gid=0";
        
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'header' => 'User-Agent: TagGenerator/1.0',
                'timeout' => 10
            ]
        ]);
        
        $csvData = @file_get_contents($csvUrl, false, $context);
        
        if ($csvData === false) {
            throw new Exception('スプレッドシートにアクセスできません。公開設定を確認してください。');
        }
        
        // CSVを解析
        $lines = array_filter(explode("\n", $csvData));
        if (count($lines) < 2) {
            throw new Exception('スプレッドシートが空または形式が正しくありません。');
        }
        
        // ヘッダー行を取得
        $headers = str_getcsv($lines[0]);
        
        return [
            'sheet_id' => $sheetId,
            'headers' => $headers,
            'rows' => count($lines) - 1,
            'sample_data' => isset($lines[1]) ? str_getcsv($lines[1]) : null
        ];
    }
    
    throw new Exception('有効なGoogle SheetsのURLではありません。');
}

// AI API呼び出し（シミュレーション）
function callAIAPI($provider, $prompt, $videoData) {
    // 実際のAPI呼び出しの代わりにシミュレーション
    $title = $videoData['title'] ?? '';
    $skill = $videoData['skill'] ?? '';
    
    $tags = [];
    
    // タイトルベースのタグ生成
    if (strpos($title, 'プレゼン') !== false) {
        $tags = array_merge($tags, ['プレゼンテーション', 'スピーチ', '発表技法', '聴衆分析']);
    }
    if (strpos($title, 'マーケティング') !== false) {
        $tags = array_merge($tags, ['マーケティング', 'SEO', 'デジタル戦略', 'ブランディング']);
    }
    if (strpos($title, 'チーム') !== false) {
        $tags = array_merge($tags, ['チームワーク', 'リーダーシップ', 'コラボレーション']);
    }
    
    // スキルベースのタグ
    if (strpos($skill, 'コミュニケーション') !== false) {
        $tags = array_merge($tags, ['コミュニケーション', '対人スキル', '説得力']);
    }
    
    // プロバイダー固有のタグ
    switch ($provider) {
        case 'openai':
            $tags = array_merge($tags, ['AI分析', '自然言語処理']);
            break;
        case 'claude':
            $tags = array_merge($tags, ['論理的思考', '構造化分析']);
            break;
        case 'gemini':
            $tags = array_merge($tags, ['多角的視点', '創造的思考']);
            break;
    }
    
    // 基本的なビジネスタグを追加
    $tags = array_merge($tags, ['ビジネススキル', '職場効率', '成果向上']);
    
    return array_unique(array_slice($tags, 0, 15));
}

// メインの処理
try {
    $method = $_SERVER['REQUEST_METHOD'];
    $requestUri = $_SERVER['REQUEST_URI'];
    
    // URLパスを解析
    $path = parse_url($requestUri, PHP_URL_PATH);
    $pathParts = explode('/', trim($path, '/'));
    
    // API エンドポイントの判定
    if (end($pathParts) !== 'api.php') {
        // api.php以外のアクセスは404
        sendJsonResponse(['error' => 'Not Found'], 404);
    }
    
    // GETリクエストの処理
    if ($method === 'GET') {
        $action = $_GET['action'] ?? 'status';
        
        switch ($action) {
            case 'status':
                sendJsonResponse([
                    'status' => 'running',
                    'timestamp' => date('c'),
                    'version' => '2.0.0-php',
                    'features' => ['sheets_api', 'ai_processing', 'tag_optimization'],
                    'ai_enabled' => true,
                    'ai_engines' => ['openai', 'claude', 'gemini']
                ]);
                break;
                
            default:
                sendJsonResponse(['error' => 'Unknown action'], 400);
        }
        exit;
    }
    
    // POSTリクエストの処理
    if ($method === 'POST') {
        $input = file_get_contents('php://input');
        $data = json_decode($input, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            sendJsonResponse(['error' => 'Invalid JSON'], 400);
        }
        
        $action = $_GET['action'] ?? '';
        
        switch ($action) {
            case 'sheets_test':
                $url = $data['url'] ?? '';
                if (empty($url)) {
                    sendJsonResponse(['success' => false, 'error' => 'URLが指定されていません'], 400);
                }
                
                try {
                    $result = fetchGoogleSheetsData($url);
                    sendJsonResponse([
                        'success' => true,
                        'message' => 'Connection successful',
                        'sheet_id' => $result['sheet_id'],
                        'rows' => $result['rows'],
                        'columns' => $result['headers'],
                        'sample_data' => $result['sample_data']
                    ]);
                } catch (Exception $e) {
                    sendJsonResponse(['success' => false, 'error' => $e->getMessage()]);
                }
                break;
                
            case 'sheets_data':
                // サンプルデータを返す
                sendJsonResponse([
                    'success' => true,
                    'data' => [
                        [
                            'title' => '効果的なプレゼンテーション技法',
                            'skill' => 'コミュニケーション',
                            'description' => '聴衆を惹きつけるプレゼンテーション技法を学ぶ',
                            'summary' => 'プレゼンテーションの基本構成と効果的な伝達方法',
                            'transcript' => 'プレゼンテーションにおいて最も重要なのは...'
                        ],
                        [
                            'title' => 'デジタルマーケティング基礎',
                            'skill' => 'マーケティング',
                            'description' => 'SEOとSNS活用による効果的なデジタルマーケティング戦略',
                            'summary' => 'デジタル時代のマーケティング手法と実践方法',
                            'transcript' => 'デジタルマーケティングの核心は顧客との接点を...'
                        ]
                    ],
                    'total_rows' => 400,
                    'processed_rows' => 2
                ]);
                break;
                
            case 'ai_process':
                $videoData = $data['data'] ?? [];
                $aiEngine = $data['ai_engine'] ?? 'openai';
                
                $results = [];
                $startTime = microtime(true);
                
                foreach ($videoData as $video) {
                    $tags = callAIAPI($aiEngine, '', $video);
                    $results[] = [
                        'title' => $video['title'] ?? '',
                        'generated_tags' => $tags,
                        'confidence' => 0.85 + (count($tags) * 0.01),
                        'processing_time' => microtime(true) - $startTime
                    ];
                }
                
                sendJsonResponse([
                    'success' => true,
                    'results' => $results,
                    'total_tags_generated' => array_sum(array_map(function($r) { return count($r['generated_tags']); }, $results)),
                    'ai_engine' => $aiEngine,
                    'processing_time' => microtime(true) - $startTime,
                    'ai_mode' => 'simulation'
                ]);
                break;
                
            case 'tags_optimize':
                $allTags = $data['tags'] ?? [];
                $maxTags = $data['max_tags'] ?? 200;
                
                // タグの頻度を計算
                $tagFrequency = [];
                foreach ($allTags as $tagList) {
                    foreach ($tagList as $tag) {
                        $tagFrequency[$tag] = ($tagFrequency[$tag] ?? 0) + 1;
                    }
                }
                
                // 頻度順にソート
                arsort($tagFrequency);
                $optimized = array_slice($tagFrequency, 0, $maxTags, true);
                
                sendJsonResponse([
                    'success' => true,
                    'original_count' => count(array_unique(array_merge(...$allTags))),
                    'optimized_count' => count($optimized),
                    'optimized_tags' => array_keys($optimized),
                    'tag_frequencies' => array_slice($optimized, 0, 20, true)
                ]);
                break;
                
            default:
                sendJsonResponse(['error' => 'Unknown action'], 400);
        }
        exit;
    }
    
    sendJsonResponse(['error' => 'Method not allowed'], 405);
    
} catch (Exception $e) {
    error_log("API Error: " . $e->getMessage());
    sendJsonResponse(['error' => $e->getMessage()], 500);
}
?>