<?php

declare(strict_types=1);

use Mds\Natcash\Config;
use Mds\Natcash\Natcash;
use Mds\Natcash\PaymentRequest;

require $argv[1].'/vendor/autoload.php';

const TIMESTAMP = 1760000000000;

function client(bool $enableFee, string $language): Natcash
{
    return new Natcash(new Config(
        'private-key-1',
        'PARTNER1',
        'FUNC1',
        'merchant',
        's3cr3t',
        'https://shop.example/natcash/callback',
        $enableFee,
        $language,
    ));
}

function call(Natcash $client, string $method, mixed ...$args): mixed
{
    $reflection = new ReflectionMethod($client, $method);

    return $reflection->invoke($client, ...$args);
}

$payments = [];
$cases = [
    ['ORDER-001', '100', null, false, true, 'ht'],
    ['ORDER-002', '250.5', null, false, true, 'ht'],
    ['ORDER-003', '10.10', null, false, true, 'ht'],
    ['ORDER-004', '0.01', null, false, true, 'ht'],
    ['ORDER-005', '1234.56', null, false, true, 'ht'],
    ['ORDER-006', '999999999.99', null, false, true, 'ht'],
    ['ORDER-007', '75', '50912345678', true, true, 'fr'],
    ['ORDER-008', '19.99', null, false, false, 'en'],
];
foreach ($cases as [$order, $amount, $msisdn, $skip, $fee, $language]) {
    $client = client($fee, $language);
    $request = new PaymentRequest($order, (float) $amount, TIMESTAMP, $msisdn, $skip);
    $payments[] = [
        'inputs' => [
            'orderNumber' => $order,
            'amount' => $amount,
            'msisdn' => $msisdn,
            'skipPhoneInput' => $skip,
            'enableFee' => $fee,
            'language' => $language,
            'timestamp' => TIMESTAMP,
        ],
        'payload' => call($client, 'getPaymentDataArray', $request),
    ];
}

$default = client(true, 'ht');

$transactions = [];
foreach (['ORDER-001', 'ORDER-XYZ-42'] as $order) {
    $transactions[] = [
        'inputs' => ['orderNumber' => $order],
        'payload' => call($default, 'getTransactionDataArray', $order, 'req-fixed-0001'),
    ];
}

$callbacks = [];
foreach ([['ORDER-001', 1], ['ORDER-002', -1], ['ORDER-003', -3]] as [$order, $code]) {
    $callbacks[] = [
        'order_number' => $order,
        'code' => $code,
        'signature' => call($default, 'generatePayloadValidationSignature', $order, $code),
    ];
}

echo json_encode(
    ['payments' => $payments, 'transactions' => $transactions, 'callbacks' => $callbacks],
    JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES,
), "\n";
