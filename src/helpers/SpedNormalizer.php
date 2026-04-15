<?php

class SpedNormalizer {

    public static function separarParticipantes(array $dados): array {

        $clientes = [];
        $fornecedores = [];

        foreach (array_unique($dados['clientes']) as $cod) {
            if (isset($dados['participantes'][$cod])) {
                $clientes[] = $dados['participantes'][$cod];
            }
        }

        foreach (array_unique($dados['fornecedores']) as $cod) {
            if (isset($dados['participantes'][$cod])) {
                $fornecedores[] = $dados['participantes'][$cod];
            }
        }

        $dados['clientes'] = $clientes;
        $dados['fornecedores'] = $fornecedores;

        return $dados;
    }
}