<?php

class SpedValidator {

    public static function validar(array $dados): array {

        $erros = [];

        if (empty($dados['empresa']['cnpj'])) {
            $erros[] = 'CNPJ da empresa não encontrado (registro 0000)';
        }

        foreach ($dados['itens'] as $i => $item) {
            if (strlen($item['cfop']) !== 4) {
                $erros[] = "CFOP inválido no item {$i}";
            }
        }

        return $erros;
    }
}