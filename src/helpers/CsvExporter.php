<?php

class CsvExporter {

    public static function export(array $dados, string $nomeArquivo) {

        header('Content-Type: text/csv; charset=UTF-8');
        header('Content-Disposition: attachment; filename="' . $nomeArquivo . '"');

        $output = fopen('php://output', 'w');

        // BOM para Excel
        fprintf($output, chr(0xEF).chr(0xBB).chr(0xBF));

        if (empty($dados)) {
            fclose($output);
            exit;
        }

        // Cabeçalho
        fputcsv($output, array_keys(current($dados)), ';');

        // Dados
        foreach ($dados as $linha) {
            fputcsv($output, $linha, ';');
        }

        fclose($output);
        exit;
    }
}