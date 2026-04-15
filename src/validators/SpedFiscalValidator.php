<?php

class SpedFiscalValidator {

    public static function validar(array $dados): array {

        $erros = [];
        $avisos = [];

        if (empty($dados['empresa']['cnpj'])) {
            $erros[] = 'Empresa sem CNPJ (Registro 0000)';
        }

        if (!isset($dados['inventario']['data'])) {
            $avisos[] = 'Inventário não informado (Bloco H)';
        }

        foreach ($dados['itens'] as $i => $item) {

            if (strlen($item['cfop']) !== 4) {
                $erros[] = "CFOP inválido no item {$i}";
            }

            if (!preg_match('/^[1-7]/', $item['cfop'])) {
                $erros[] = "CFOP incoerente: {$item['cfop']}";
            }
        }

        return [
            'erros' => $erros,
            'avisos' => $avisos
        ];
    }
}