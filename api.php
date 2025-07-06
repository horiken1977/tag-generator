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
                'header' => [
                    'User-Agent: TagGenerator/1.0',
                    'Accept: text/csv,*/*'
                ],
                'timeout' => 15
            ]
        ]);
        
        $csvData = @file_get_contents($csvUrl, false, $context);
        
        if ($csvData === false) {
            throw new Exception('スプレッドシートにアクセスできません。公開設定を確認してください。');
        }
        
        // 文字エンコーディングをUTF-8に統一
        $csvData = mb_convert_encoding($csvData, 'UTF-8', 'auto');
        
        // CSVを適切に解析 - fgetcsvを使用してより正確な解析
        $csvResource = fopen('data://text/plain,' . urlencode($csvData), 'r');
        if (!$csvResource) {
            throw new Exception('CSVデータの解析に失敗しました。');
        }
        
        $allRows = [];
        while (($row = fgetcsv($csvResource)) !== false) {
            if (!empty(array_filter($row, function($cell) { return trim($cell) !== ''; }))) {
                $allRows[] = $row;
            }
        }
        fclose($csvResource);
        
        if (count($allRows) < 1) {
            throw new Exception('スプレッドシートが空です。');
        }
        
        // ヘッダー行を取得（最初の行）
        $headers = $allRows[0];
        
        // ヘッダーの前後の空白を除去
        $headers = array_map(function($header) {
            return trim($header);
        }, $headers);
        
        // 空のヘッダーを除去
        $headers = array_filter($headers, function($header) {
            return $header !== '';
        });
        
        // サンプルデータを取得（2行目があれば）
        $sampleData = null;
        if (count($allRows) > 1) {
            $sampleData = array_map('trim', $allRows[1]);
        }
        
        // デバッグ情報をログに記録
        error_log("CSV Headers count: " . count($headers));
        error_log("CSV Headers: " . json_encode($headers, JSON_UNESCAPED_UNICODE));
        error_log("CSV Total rows: " . count($allRows));
        error_log("Raw first row: " . json_encode($allRows[0], JSON_UNESCAPED_UNICODE));
        error_log("Headers after processing: " . print_r($headers, true));
        error_log("Raw CSV data first 500 chars: " . substr($csvData, 0, 500));
        
        // 各ヘッダーの詳細情報
        foreach ($headers as $i => $header) {
            error_log("Header $i: '" . $header . "' (length: " . strlen($header) . ", bytes: " . mb_strlen($header, 'UTF-8') . ")");
        }
        
        return [
            'sheet_id' => $sheetId,
            'headers' => array_values($headers), // インデックスを再整理
            'rows' => count($allRows) - 1,
            'sample_data' => $sampleData,
            'debug_info' => [
                'raw_header_line' => json_encode($allRows[0], JSON_UNESCAPED_UNICODE),
                'total_lines' => count($allRows),
                'csv_size' => strlen($csvData),
                'header_count' => count($headers)
            ]
        ];
    }
    
    throw new Exception('有効なGoogle SheetsのURLではありません。');
}

// ステップ1: 軽量バッチ処理（プログレッシブ処理）
function processLightweightBatch($videoData, $aiEngine, $batchSize, $quality, $useRealAI) {
    $results = [];
    $processedCount = 0;
    $maxItemsPerBatch = 5; // さらに小さなバッチサイズ
    
    // データを非常に小さなチャンクに分割
    $totalItems = count($videoData);
    
    for ($i = 0; $i < $totalItems; $i += $maxItemsPerBatch) {
        $chunk = array_slice($videoData, $i, $maxItemsPerBatch);
        
        foreach ($chunk as $video) {
            // 軽量データのみを使用（文字起こしを除外）
            $lightweightVideo = [
                'title' => substr($video['title'] ?? '', 0, 100), // タイトルも100文字に制限
                'skill' => substr($video['skill'] ?? '', 0, 50),   // スキルも50文字に制限
                'description' => substr($video['description'] ?? '', 0, 200) // 説明も200文字に制限
                // 文字起こしは意図的に除外
            ];
            
            $tags = callAIAPI($aiEngine, '', $lightweightVideo);
            $results[] = [
                'title' => $video['title'] ?? '',
                'generated_tags' => $tags,
                'confidence' => 0.75 + (count($tags) * 0.01),
                'processing_type' => 'lightweight',
                'batch_index' => intval($i / $maxItemsPerBatch)
            ];
            
            $processedCount++;
            
            // レート制限対策とメモリ管理
            if ($useRealAI) {
                usleep(100000); // 0.1秒の遅延
            }
            
            // メモリ使用量の監視
            if (memory_get_usage() > 128 * 1024 * 1024) { // 128MBで制限
                error_log("Memory limit reached, processed: $processedCount items");
                break 2;
            }
        }
        
        // バッチ間の小休止
        usleep(50000); // 0.05秒
    }
    
    return $results;
}

// ステップ2: 重要動画の個別処理
function processDetailedIndividual($importantVideos, $aiEngine, $quality, $useRealAI) {
    $results = [];
    
    foreach ($importantVideos as $video) {
        // 文字起こしを含めた詳細処理
        $detailedVideo = [
            'title' => $video['title'] ?? '',
            'skill' => $video['skill'] ?? '',
            'description' => $video['description'] ?? '',
            'summary' => $video['summary'] ?? '',
            'transcript' => isset($video['transcript']) ? substr($video['transcript'], 0, 2000) : '' // 2000文字に制限
        ];
        
        $tags = callAIAPI($aiEngine, '', $detailedVideo);
        $results[] = [
            'title' => $video['title'] ?? '',
            'generated_tags' => $tags,
            'confidence' => 0.90 + (count($tags) * 0.005), // 詳細処理なので信頼度は高め
            'processing_type' => 'detailed'
        ];
        
        // 個別処理なので長めの遅延
        if ($useRealAI) {
            usleep(200000); // 0.2秒の遅延
        }
    }
    
    return $results;
}

// ステップ3: タグ統合処理
function unifyTags($lightweightTags, $detailedTags, $maxTags) {
    $allTags = [];
    $tagFrequency = [];
    $tagSources = [];
    
    // 軽量処理のタグを収集
    foreach ($lightweightTags as $result) {
        foreach ($result['generated_tags'] as $tag) {
            $normalizedTag = normalizeTag($tag);
            $tagFrequency[$normalizedTag] = ($tagFrequency[$normalizedTag] ?? 0) + 1;
            $tagSources[$normalizedTag]['lightweight'] = ($tagSources[$normalizedTag]['lightweight'] ?? 0) + 1;
        }
    }
    
    // 詳細処理のタグを収集（重み付けして追加）
    foreach ($detailedTags as $result) {
        foreach ($result['generated_tags'] as $tag) {
            $normalizedTag = normalizeTag($tag);
            $tagFrequency[$normalizedTag] = ($tagFrequency[$normalizedTag] ?? 0) + 2; // 詳細処理のタグは2倍の重み
            $tagSources[$normalizedTag]['detailed'] = ($tagSources[$normalizedTag]['detailed'] ?? 0) + 1;
        }
    }
    
    // タグの類似度による統合
    $unifiedTags = unifySimilarTags($tagFrequency);
    
    // 重要度順にソート
    arsort($unifiedTags);
    
    // 上位タグを選択
    $finalTags = array_slice($unifiedTags, 0, $maxTags, true);
    
    return [
        [
            'unified_tags' => array_keys($finalTags),
            'tag_frequencies' => $finalTags,
            'tag_sources' => $tagSources,
            'processing_type' => 'unified',
            'original_count' => count($tagFrequency),
            'unified_count' => count($finalTags)
        ]
    ];
}

// タグ正規化関数
function normalizeTag($tag) {
    // 類似タグの統一
    $synonyms = [
        'マーケティング' => ['デジタルマーケティング', 'ネットマーケティング', 'Webマーケティング'],
        'コミュニケーション' => ['コミュニケーション能力', '対人コミュニケーション'],
        'プレゼンテーション' => ['プレゼン', 'プレゼンスキル', '発表'],
        'リーダーシップ' => ['リーダー', 'リーダー力', 'リーダーシップスキル'],
        'チームワーク' => ['チーム力', 'チームビルディング'],
        'ビジネススキル' => ['ビジネス能力', 'ビジネス力']
    ];
    
    $normalizedTag = trim($tag);
    
    // 同義語辞書でチェック
    foreach ($synonyms as $master => $variations) {
        if (in_array($normalizedTag, $variations)) {
            return $master;
        }
    }
    
    return $normalizedTag;
}

// 類似タグの統合
function unifySimilarTags($tagFrequency) {
    $unified = [];
    $processed = [];
    
    foreach ($tagFrequency as $tag => $freq) {
        if (in_array($tag, $processed)) {
            continue;
        }
        
        $similarTags = findSimilarTags($tag, array_keys($tagFrequency));
        $totalFreq = $freq;
        $processed[] = $tag;
        
        foreach ($similarTags as $similarTag) {
            if ($similarTag !== $tag && !in_array($similarTag, $processed)) {
                $totalFreq += $tagFrequency[$similarTag];
                $processed[] = $similarTag;
            }
        }
        
        $unified[$tag] = $totalFreq;
    }
    
    return $unified;
}

// 類似タグの検出
function findSimilarTags($baseTag, $allTags) {
    $similar = [];
    
    foreach ($allTags as $tag) {
        // レーベンシュタイン距離による類似度計算
        $distance = levenshtein($baseTag, $tag);
        $maxLength = max(mb_strlen($baseTag), mb_strlen($tag));
        
        if ($maxLength > 0) {
            $similarity = 1 - ($distance / $maxLength);
            
            // 85%以上の類似度で統合対象とする
            if ($similarity >= 0.85 && $similarity < 1.0) {
                $similar[] = $tag;
            }
        }
    }
    
    return $similar;
}

// AI API呼び出し
function callAIAPI($provider, $prompt, $videoData) {
    $apiKey = getApiKey($provider);
    if (!$apiKey) {
        // APIキーがない場合はシミュレーションモードで動作
        return generateSimulatedTags($videoData);
    }
    
    // プロンプトの作成
    $systemPrompt = "あなたはマーケティング教育動画のタグ生成専門家です。動画の内容を分析し、検索性と分類に最適な15個のタグを生成してください。";
    
    $userPrompt = "以下の動画情報から、最も適切なタグを15個生成してください。\n\n";
    $userPrompt .= "タイトル: " . ($videoData['title'] ?? '') . "\n";
    $userPrompt .= "スキル: " . ($videoData['skill'] ?? '') . "\n";
    
    if (!empty($videoData['description'])) {
        $userPrompt .= "説明: " . $videoData['description'] . "\n";
    }
    if (!empty($videoData['summary'])) {
        $userPrompt .= "要約: " . $videoData['summary'] . "\n";
    }
    if (!empty($videoData['transcript']) && strlen($videoData['transcript']) < 2000) {
        $userPrompt .= "内容抜粋: " . substr($videoData['transcript'], 0, 2000) . "\n";
    }
    
    $userPrompt .= "\nタグは日本語で、具体的かつ検索しやすい形式で生成してください。カンマ区切りで出力してください。";
    
    try {
        switch ($provider) {
            case 'openai':
                return callOpenAIForTags($apiKey, $systemPrompt, $userPrompt);
            case 'claude':
                return callClaudeForTags($apiKey, $systemPrompt, $userPrompt);
            case 'gemini':
                return callGeminiForTags($apiKey, $userPrompt);
            default:
                return generateSimulatedTags($videoData);
        }
    } catch (Exception $e) {
        error_log("AI API Error: " . $e->getMessage());
        // エラーの場合はシミュレーションにフォールバック
        return generateSimulatedTags($videoData);
    }
}

// シミュレーションタグ生成
function generateSimulatedTags($videoData) {
    $title = $videoData['title'] ?? '';
    $skill = $videoData['skill'] ?? '';
    
    $tags = [];
    
    // スキルベースのタグ
    if (!empty($skill)) {
        $tags[] = $skill;
    }
    
    // タイトルベースのタグ生成
    if (strpos($title, 'プレゼン') !== false) {
        $tags = array_merge($tags, ['プレゼンテーション', 'スピーチ', '発表技法']);
    }
    if (strpos($title, 'マーケティング') !== false) {
        $tags = array_merge($tags, ['マーケティング', 'デジタルマーケティング', 'SEO']);
    }
    if (strpos($title, 'チーム') !== false) {
        $tags = array_merge($tags, ['チームワーク', 'リーダーシップ']);
    }
    
    // 基本的なビジネスタグを追加
    $tags = array_merge($tags, ['ビジネススキル', '職場効率']);
    
    return array_unique(array_slice($tags, 0, 15));
}

// OpenAI API呼び出し
function callOpenAIForTags($apiKey, $systemPrompt, $userPrompt) {
    $url = 'https://api.openai.com/v1/chat/completions';
    
    $headers = [
        'Authorization: Bearer ' . $apiKey,
        'Content-Type: application/json'
    ];
    
    $data = [
        'model' => 'gpt-3.5-turbo',
        'messages' => [
            ['role' => 'system', 'content' => $systemPrompt],
            ['role' => 'user', 'content' => $userPrompt]
        ],
        'max_tokens' => 200,
        'temperature' => 0.7
    ];
    
    $response = makeHTTPRequest($url, $headers, $data);
    
    if (isset($response['choices'][0]['message']['content'])) {
        $tagsString = $response['choices'][0]['message']['content'];
        return array_map('trim', explode(',', $tagsString));
    }
    
    throw new Exception('Invalid OpenAI response');
}

// Claude API呼び出し
function callClaudeForTags($apiKey, $systemPrompt, $userPrompt) {
    $url = 'https://api.anthropic.com/v1/messages';
    
    $headers = [
        'x-api-key: ' . $apiKey,
        'Content-Type: application/json',
        'anthropic-version: 2023-06-01'
    ];
    
    $data = [
        'model' => 'claude-3-haiku-20240307',
        'messages' => [
            ['role' => 'user', 'content' => $systemPrompt . "\n\n" . $userPrompt]
        ],
        'max_tokens' => 200
    ];
    
    $response = makeHTTPRequest($url, $headers, $data);
    
    if (isset($response['content'][0]['text'])) {
        $tagsString = $response['content'][0]['text'];
        return array_map('trim', explode(',', $tagsString));
    }
    
    throw new Exception('Invalid Claude response');
}

// Gemini API呼び出し
function callGeminiForTags($apiKey, $userPrompt) {
    $url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=' . $apiKey;
    
    $headers = [
        'Content-Type: application/json'
    ];
    
    $data = [
        'contents' => [
            [
                'parts' => [
                    ['text' => $userPrompt]
                ]
            ]
        ],
        'generationConfig' => [
            'maxOutputTokens' => 200,
            'temperature' => 0.7
        ]
    ];
    
    $response = makeHTTPRequest($url, $headers, $data);
    
    if (isset($response['candidates'][0]['content']['parts'][0]['text'])) {
        $tagsString = $response['candidates'][0]['content']['parts'][0]['text'];
        return array_map('trim', explode(',', $tagsString));
    }
    
    throw new Exception('Invalid Gemini response');
}

// HTTP リクエスト実行
function makeHTTPRequest($url, $headers, $data) {
    $ch = curl_init($url);
    
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => true
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    
    curl_close($ch);
    
    if ($error) {
        throw new Exception('cURL error: ' . $error);
    }
    
    if ($httpCode >= 400) {
        $errorData = json_decode($response, true);
        $errorMessage = $errorData['error']['message'] ?? 'HTTP error: ' . $httpCode;
        throw new Exception($errorMessage);
    }
    
    $decodedResponse = json_decode($response, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('Invalid JSON response');
    }
    
    return $decodedResponse;
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
                $url = $data['url'] ?? '';
                $columnMapping = $data['column_mapping'] ?? [];
                
                if (empty($url)) {
                    sendJsonResponse(['success' => false, 'error' => 'URLが指定されていません'], 400);
                }
                
                try {
                    // スプレッドシートからCSVデータを取得
                    $sheetData = fetchGoogleSheetsData($url);
                    $headers = $sheetData['headers'];
                    
                    // CSV全体を再度取得して全データを処理
                    $sheetId = $sheetData['sheet_id'];
                    $csvUrl = "https://docs.google.com/spreadsheets/d/{$sheetId}/export?format=csv&gid=0";
                    
                    $context = stream_context_create([
                        'http' => [
                            'method' => 'GET',
                            'header' => [
                                'User-Agent: TagGenerator/1.0',
                                'Accept: text/csv,*/*'
                            ],
                            'timeout' => 30
                        ]
                    ]);
                    
                    $csvData = @file_get_contents($csvUrl, false, $context);
                    if ($csvData === false) {
                        throw new Exception('スプレッドシートデータの取得に失敗しました。');
                    }
                    
                    // 文字エンコーディングをUTF-8に統一
                    $csvData = mb_convert_encoding($csvData, 'UTF-8', 'auto');
                    
                    // CSVを解析
                    $csvResource = fopen('data://text/plain,' . urlencode($csvData), 'r');
                    if (!$csvResource) {
                        throw new Exception('CSVデータの解析に失敗しました。');
                    }
                    
                    $allRows = [];
                    $rowIndex = 0;
                    while (($row = fgetcsv($csvResource)) !== false) {
                        if ($rowIndex === 0) {
                            // ヘッダー行はスキップ
                            $rowIndex++;
                            continue;
                        }
                        
                        // 空行をスキップ
                        if (empty(array_filter($row, function($cell) { return trim($cell) !== ''; }))) {
                            continue;
                        }
                        
                        // 列マッピングに基づいてデータを構造化
                        $mappedData = [];
                        
                        if (isset($columnMapping['title']) && isset($row[$columnMapping['title']])) {
                            $mappedData['title'] = trim($row[$columnMapping['title']]);
                        }
                        if (isset($columnMapping['skill']) && isset($row[$columnMapping['skill']])) {
                            $mappedData['skill'] = trim($row[$columnMapping['skill']]);
                        }
                        if (isset($columnMapping['description']) && isset($row[$columnMapping['description']])) {
                            $mappedData['description'] = trim($row[$columnMapping['description']]);
                        }
                        if (isset($columnMapping['summary']) && isset($row[$columnMapping['summary']])) {
                            $mappedData['summary'] = trim($row[$columnMapping['summary']]);
                        }
                        if (isset($columnMapping['transcript']) && isset($row[$columnMapping['transcript']])) {
                            $mappedData['transcript'] = trim($row[$columnMapping['transcript']]);
                        }
                        
                        // 必須フィールドが存在する場合のみ追加
                        if (!empty($mappedData['title']) && !empty($mappedData['skill'])) {
                            $allRows[] = $mappedData;
                        }
                        
                        $rowIndex++;
                    }
                    fclose($csvResource);
                    
                    sendJsonResponse([
                        'success' => true,
                        'data' => $allRows,
                        'total_rows' => count($allRows),
                        'processed_rows' => count($allRows)
                    ]);
                    
                } catch (Exception $e) {
                    sendJsonResponse(['success' => false, 'error' => $e->getMessage()]);
                }
                break;
                
            case 'ai_process':
                // リクエストサイズの事前チェック
                $requestSize = strlen(json_encode($data));
                error_log("AI Process request size: " . $requestSize . " bytes");
                
                if ($requestSize > 512 * 1024) { // 512KB制限
                    sendJsonResponse(['success' => false, 'error' => 'リクエストサイズが大きすぎます。データを分割してください。'], 413);
                    break;
                }
                
                $videoData = $data['data'] ?? [];
                $aiEngine = $data['ai_engine'] ?? 'openai';
                $processingMode = $data['processing_mode'] ?? 'lightweight';
                $batchSize = intval($data['batch_size'] ?? 5); // デフォルトバッチサイズを5に縮小
                $quality = $data['quality'] ?? 'balanced';
                $useRealAI = $data['use_real_ai'] ?? false;
                
                $results = [];
                $startTime = microtime(true);
                $processedCount = 0;
                
                // タイムアウト設定
                set_time_limit(300); // 5分のタイムアウト
                
                switch ($processingMode) {
                    case 'lightweight':
                        // ステップ1: 軽量バッチ処理（タイトル + スキル + 説明文のみ）
                        if (count($videoData) > 50) {
                            // 大量データの場合は最初の50件のみ処理
                            $videoData = array_slice($videoData, 0, 50);
                            error_log("Large dataset detected, processing first 50 items only");
                        }
                        $results = processLightweightBatch($videoData, $aiEngine, $batchSize, $quality, $useRealAI);
                        $processedCount = count($results);
                        break;
                        
                    case 'detailed':
                        // ステップ2: 重要動画の個別処理（文字起こし含む）
                        $importantVideos = $data['important_videos'] ?? [];
                        if (count($importantVideos) > 20) {
                            // 詳細処理は最大20件に制限
                            $importantVideos = array_slice($importantVideos, 0, 20);
                        }
                        $results = processDetailedIndividual($importantVideos, $aiEngine, $quality, $useRealAI);
                        $processedCount = count($results);
                        break;
                        
                    case 'unified':
                        // ステップ3: タグ統合処理
                        $lightweightTags = $data['lightweight_tags'] ?? [];
                        $detailedTags = $data['detailed_tags'] ?? [];
                        $results = unifyTags($lightweightTags, $detailedTags, $data['max_tags'] ?? 200);
                        $processedCount = count($results);
                        break;
                        
                    default:
                        throw new Exception('Unknown processing mode: ' . $processingMode);
                }
                
                // AI モードの判定
                $apiKey = getApiKey($aiEngine);
                $aiMode = $apiKey ? 'real' : 'simulation';
                
                sendJsonResponse([
                    'success' => true,
                    'results' => $results,
                    'total_tags_generated' => array_sum(array_map(function($r) { 
                        return is_array($r['generated_tags'] ?? []) ? count($r['generated_tags']) : 0; 
                    }, $results)),
                    'ai_engine' => $aiEngine,
                    'processing_time' => microtime(true) - $startTime,
                    'ai_mode' => $aiMode,
                    'processed_count' => $processedCount,
                    'processing_mode' => $processingMode,
                    'batch_size' => $batchSize,
                    'quality' => $quality,
                    'request_size' => $requestSize
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