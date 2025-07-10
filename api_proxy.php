<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

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
            'timeout' => 30
        ]
    ]);
} else {
    $context = stream_context_create([
        'http' => [
            'method' => $method,
            'header' => implode("\r\n", $headers),
            'timeout' => 30
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