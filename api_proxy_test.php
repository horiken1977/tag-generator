<?php
// シンプルテスト版 - 最小限の機能でテスト
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER["REQUEST_METHOD"] === "OPTIONS") {
    exit(0);
}

$path = $_GET["path"] ?? "";

// /api/ai/stage1 のテスト用レスポンス
if ($path === "/api/ai/stage1") {
    echo json_encode([
        "stage" => 1,
        "success" => true,
        "tag_candidates" => [
            "Google Analytics",
            "ROI",
            "CPA",
            "PDCAサイクル",
            "Instagram",
            "エンゲージメント率"
        ],
        "candidate_count" => 6,
        "processing_time" => 2.5,
        "message" => "テストモード: タグ候補が生成されました"
    ]);
    exit(0);
}

// その他のエンドポイントは通常のプロキシとして動作
$api_base = "http://localhost:8080";
$url = $api_base . "/" . ltrim($path, "/");

$method = $_SERVER["REQUEST_METHOD"];
$options = [
    "http" => [
        "method" => $method,
        "header" => "Content-Type: application/json
",
        "timeout" => 30,
        "ignore_errors" => true
    ]
];

if ($method === "POST") {
    $postData = file_get_contents("php://input");
    $options["http"]["content"] = $postData;
}

$context = stream_context_create($options);
$result = @file_get_contents($url, false, $context);

if ($result === false) {
    http_response_code(503);
    echo json_encode([
        "success" => false,
        "error" => "API server unavailable"
    ]);
} else {
    echo $result;
}
?>
