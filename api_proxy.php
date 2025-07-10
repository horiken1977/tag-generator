<?php
// エラーログを有効化
error_reporting(E_ALL);
ini_set('log_errors', 1);
ini_set('error_log', 'api_proxy_error.log');

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// デバッグログ
file_put_contents('api_proxy_debug.log', date('Y-m-d H:i:s') . " - Request: " . $_SERVER['REQUEST_METHOD'] . " " . ($_GET['path'] ?? 'NO_PATH') . "\n", FILE_APPEND);

$api_base = 'http://localhost:8080';
$path = $_GET['path'] ?? '';
$url = $api_base . '/' . ltrim($path, '/');

$method = $_SERVER['REQUEST_METHOD'];
$headers = ['Content-Type: application/json'];

if ($method === 'POST') {
    $postData = file_get_contents('php://input');
    
    $context = stream_context_create([
        'http' => [
            'method' => $method,
            'header' => implode("\r\n", $headers),
            'content' => $postData,
            'timeout' => 120,  // タイムアウトを120秒に延長
            'ignore_errors' => true
        ]
    ]);
} else {
    $context = stream_context_create([
        'http' => [
            'method' => $method,
            'header' => implode("\r\n", $headers),
            'timeout' => 120,  // タイムアウトを120秒に延長
            'ignore_errors' => true
        ]
    ]);
}

$result = @file_get_contents($url, false, $context);

if ($result === false) {
    http_response_code(503);
    echo json_encode([
        'success' => false,
        'error' => 'API server unavailable',
        'debug_info' => [
            'url' => $url,
            'method' => $method
        ]
    ]);
} else {
    $http_response_header = $http_response_header ?? [];
    foreach ($http_response_header as $header) {
        if (strpos($header, 'HTTP/') === 0) {
            $status_code = intval(substr($header, 9, 3));
            http_response_code($status_code);
        }
    }
    echo $result;
}
?>