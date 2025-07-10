<?php
// 直接stage1を処理するPHPスクリプト（プロキシを使わない）
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit();
}

// POSTデータを取得
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || !isset($data['data'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data']);
    exit();
}

$video_data = $data['data'];
$video_count = count($video_data);

// バッチサイズ制限
$max_batch_size = 50;
if ($video_count > $max_batch_size) {
    $video_data = array_slice($video_data, 0, $max_batch_size);
    $video_count = $max_batch_size;
}

// データ集約
$all_titles = [];
$all_skills = [];
$all_descriptions = [];
$all_summaries = [];

foreach ($video_data as $video) {
    if (isset($video['title'])) $all_titles[] = $video['title'];
    if (isset($video['skill'])) $all_skills[] = $video['skill'];
    if (isset($video['description'])) $all_descriptions[] = $video['description'];
    if (isset($video['summary'])) $all_summaries[] = $video['summary'];
}

// キーワード抽出（PHPでの簡易実装）
$keywords = [];

// タイトルからキーワード抽出
$title_text = implode(' ', $all_titles);
preg_match_all('/[A-Z][a-zA-Z]*|[ァ-ヶー]+|[一-龯]{2,}/u', $title_text, $matches);
foreach ($matches[0] as $match) {
    if (strlen($match) >= 3) {
        $keywords[] = $match;
    }
}

// 既知の重要キーワードを追加
$important_keywords = [
    'Google Analytics', 'ROI', 'CPA', 'PDCAサイクル', 
    'Instagram', 'Facebook', 'Twitter', 'TikTok',
    'SEO', 'SEM', 'KPI', 'OKR', 'A/Bテスト',
    'エンゲージメント率', 'コンバージョン率', 'CTR', 'CPM'
];

foreach ($important_keywords as $keyword) {
    if (stripos($title_text . ' ' . implode(' ', $all_descriptions), $keyword) !== false) {
        $keywords[] = $keyword;
    }
}

// 重複除去と汎用語フィルタリング
$keywords = array_unique($keywords);
$filtered_keywords = [];

$generic_words = [
    '要素', '分類', 'ポイント', '手法', '方法', '技術',
    '基本', '応用', '実践', '理論', '概要', '入門'
];

foreach ($keywords as $keyword) {
    $is_generic = false;
    foreach ($generic_words as $generic) {
        if (strpos($keyword, $generic) !== false) {
            $is_generic = true;
            break;
        }
    }
    if (!$is_generic && !preg_match('/\d+つの/', $keyword)) {
        $filtered_keywords[] = $keyword;
    }
}

// 最大30個に制限
$filtered_keywords = array_slice($filtered_keywords, 0, 30);

// レスポンス
$response = [
    'stage' => 1,
    'success' => true,
    'tag_candidates' => array_values($filtered_keywords),
    'candidate_count' => count($filtered_keywords),
    'processing_time' => 1.5,
    'source_data_stats' => [
        'total_videos' => $video_count,
        'titles_processed' => count($all_titles),
        'skills_processed' => count($all_skills),
        'descriptions_processed' => count($all_descriptions),
        'summaries_processed' => count($all_summaries),
        'transcripts_excluded' => true
    ],
    'message' => 'タグ候補が生成されました（PHP簡易版）。内容を確認して承認してください。'
];

echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>