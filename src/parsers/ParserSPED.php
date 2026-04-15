<?php
require_once __DIR__ . '/../helpers/SpedUtils.php';

class ParserSPED {

    public function parse(string $arquivo): array {

        $linhas = file($arquivo, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

        $empresa = [];
        $participantes = [];
        $clientes = [];
        $fornecedores = [];
        $itens = [];
        $notas = [];
        $itens_nota = [];
        $cfop_icms = [];
        $apuracao = [];

        $notaAtual = null;

        foreach ($linhas as $linha) {

            if ($linha[0] !== '|') continue;

            $campos = explode('|', $linha);
            $reg = $campos[1];

            switch ($reg) {

                /* ===== EMPRESA ===== */
                case '0000':
                    $empresa = [
                        'CNPJ'        => $campos[7] ?? '',
                        'RazaoSocial' => $campos[6] ?? '',
                        'UF'          => $campos[10] ?? '',
                        'IE'          => $campos[11] ?? '',
                        'DataInicial' => $campos[4] ?? '',
                        'DataFinal'   => $campos[5] ?? ''
                    ];
                    break;

                /* ===== PARTICIPANTES ===== */
                
                /* =====================================================
                 * PARTICIPANTES – CLIENTES / FORNECEDORES (0150)
                 * ===================================================== */
                case '0150':

                    $codigo = $campos[2];

                    $participantes[$codigo] = [
                        'Codigo'   => $codigo,
                        'Nome'     => $campos[3] ?? '',
                        'CNPJ'     => $campos[5] ?? '',
                        'CPF'      => $campos[6] ?? '',
                        'IE'       => $campos[7] ?? '',
                        'Endereco' => $campos[10] ?? '',
                        'Numero'   => $campos[11] ?? '',
                        'Bairro'   => $campos[13] ?? '',
                        'Cidade'   => $campos[8]  ?? '', // Código do município
                        'CEP'      => '',
                        'Estado'   => $empresa['UF'] ?? ''
                    ];
                    break;

                /* ===== ITENS (0200) ===== */
                case '0200':
                    $itens[$campos[2]] = [
                        'CodigoItem' => $campos[2],
                        'Descricao'  => $campos[3],
                        'NCM'        => $campos[8] ?? '',
                        'Unidade'    => $campos[6] ?? ''
                    ];
                    break;

                /* ===== NOTAS ===== */
                case 'C100':
                    $operacao = $campos[2]; // 0 entrada | 1 saída
                    $codPart  = $campos[4];

                    $notaAtual = [
                        'Numero'       => $campos[8],
                        'Operacao'     => ($operacao === '0') ? 'Entrada' : 'Saida',
                        'Participante' => $codPart,
                        'ValorTotal'   => SpedUtils::toFloat($campos[12])
                    ];
                    $notas[] = $notaAtual;

                    if ($operacao === '0' && isset($participantes[$codPart])) {
                        $fornecedores[$codPart] = $participantes[$codPart];
                    }

                    if ($operacao === '1' && isset($participantes[$codPart])) {
                        $clientes[$codPart] = $participantes[$codPart];
                    }
                    break;

                /* ===== ITENS DA NOTA ===== */
                case 'C170':
                    if ($notaAtual) {
                        $itens_nota[] = [
                            'NumeroNF'   => $notaAtual['Numero'],
                            'CodigoItem' => $campos[3],
                            'Quantidade' => SpedUtils::toFloat($campos[4]),
                            'ValorItem'  => SpedUtils::toFloat($campos[7]),
                            'CFOP'       => $campos[11]
                        ];
                    }
                    break;

                /* ===== CFOP / ICMS ===== */
                case 'C190':
                    $cfop_icms[] = [
                        'CFOP'     => $campos[3],
                        'BaseICMS' => SpedUtils::toFloat($campos[5]),
                        'ICMS'     => SpedUtils::toFloat($campos[6])
                    ];
                    break;

                /* ===== APURAÇÃO ===== */
                case 'E110':
                    $apuracao = [
                        'ICMSRecolher' => SpedUtils::toFloat($campos[9]),
                        'SaldoCredor' => SpedUtils::toFloat($campos[11])
                    ];
                    break;
            }
        }

        return compact(
            'empresa',
            'clientes',
            'fornecedores',
            'itens',
            'notas',
            'itens_nota',
            'cfop_icms',
            'apuracao'
        );
    }
}