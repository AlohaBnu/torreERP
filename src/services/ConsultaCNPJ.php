<?php

class ReceitaService {

    public static function consultaCNPJ(string $cnpj): ?array {

        $cnpj = preg_replace('/\D/', '', $cnpj);

        if (strlen($cnpj) !== 14) {
            return null;
        }

        $url = "https://brasilapi.com.br/api/cnpj/v1/{$cnpj}";

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200 || !$response) {
            return null;
        }

        $json = json_decode($response, true);

        if (!is_array($json)) {
            return null;
        }

        return [
            'Endereco' => $json['logradouro'] ?? '',
            'Numero'   => $json['numero'] ?? '',
            'Bairro'   => $json['bairro'] ?? '',
            'CEP'      => $json['cep'] ?? '',
            'Cidade'   => $json['municipio'] ?? '',
            'Estado'   => $json['uf'] ?? '',
        ];
    }
}