<?php
require_once __DIR__.'/../src/parsers/ParserSPED.php';
require_once __DIR__.'/../src/helpers/CsvExporter.php';

$tipo = $_GET['tipo'] ?? null;
$arquivo = $_GET['arquivo'] ?? null;

if (!$tipo || !$arquivo) {
    die('Parâmetros inválidos');
}

$parser = new ParserSPED();
$dados = $parser->parse($arquivo);

switch ($tipo) {

    case 'empresa':
        CsvExporter::export([$dados['empresa']], 'empresa.csv');
        break;

    case 'participantes':
        CsvExporter::export(array_values($dados['participantes']), 'participantes.csv');
        break;

    case 'itens':
        CsvExporter::export(array_values($dados['itens']), 'itens.csv');
        break;

    case 'notas':
        CsvExporter::export($dados['notas'], 'notas.csv');
        break;

    case 'itens_nota':
        CsvExporter::export($dados['itens_nota'], 'itens_nota.csv');
        break;

    case 'cfop_icms':
        CsvExporter::export($dados['cfop_icms'], 'cfop_icms.csv');
        break;

    case 'apuracao':
        CsvExporter::export([$dados['apuracao']], 'apuracao_icms.csv');
        break;

    default:
        die('Tipo inválido');
}