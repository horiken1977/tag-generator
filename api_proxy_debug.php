<?php
// エラーログをより詳細に
error_reporting(E_ALL);
ini_set("display_errors", 1);
ini_set("log_errors", 1);
ini_set("error_log", __DIR__ . "/api_proxy_error.log");

// デバッグ情報を出力
$debug_mode = isset($_GET["debug"]) ? true : false;

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER["REQUEST_METHOD"] === "OPTIONS") {
    exit(0);
}

// デバッグログ
$log_message = date("Y-m-d H:i:s") . " - " . $_SERVER["REQUEST_METHOD"] . " " . ($_GET["path"] ?? "NO_PATH");
file_put_contents(__DIR__ . "/api_proxy_debug.log", $log_message . "
", FILE_APPEND);

$api_base = "http://localhost:8080";
$path = $_GET["path"] ?? "";
$url = $api_base . "/" . ltrim($path, "/");

$method = $_SERVER["REQUEST_METHOD"];
$headers = ["Content-Type: application/json"];

if ($method === "POST") {
    $postData = file_get_contents("php://input");
    
    // デバッグ: POSTデータのサイズをログ
    $post_size = strlen($postData);
    file_put_contents(__DIR__ . "/api_proxy_debug.log", "  POST data size: $post_size bytes
", FILE_APPEND);
    
    $context = stream_context_create([
        "http" => [
            "method" => $method,
            "header" => implode("
", $headers),
            "content" => $postData,
            "timeout" => 120,
            "ignore_errors" => true
        ]
    ]);
} else {
    $context = stream_context_create([
        "http" => [
            "method" => $method,
            "header" => implode("
", $headers),
            "timeout" => 120,
            "ignore_errors" => true
        ]
    ]);
}

// リクエスト実行
$result = @file_get_contents($url, false, $context);

// レスポンスヘッダーを取得
$response_headers = $http_response_header ?? [];
$status_code = 200;

foreach ($response_headers as $header) {
    if (strpos($header, "HTTP/") === 0) {
        $status_code = intval(substr($header, 9, 3));
        http_response_code($status_code);
    }
}

// エラーハンドリング
if ($result === false) {
    $error = error_get_last();
    $error_message = $error ? $error["message"] : "Unknown error";
    
    file_put_contents(__DIR__ . "/api_proxy_error.log", date("Y-m-d H:i:s") . " - Error: $error_message
", FILE_APPEND);
    
    http_response_code(503);
    echo json_encode([
        "success" => false,
        "error" => "API server unavailable",
        "debug_info" => [
            "url" => $url,
            "method" => $method,
            "error_detail" => $error_message
        ]
    ]);
} else {
    // デバッグ: レスポンスステータスをログ
    file_put_contents(__DIR__ . "/api_proxy_debug.log", "  Response status: $status_code
", FILE_APPEND);
    
    echo $result;
}
?>
