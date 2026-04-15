<?php

class ParserXML
{
    public function parse($file, $cnpjEmpresa = null)
    {
        $xml = simplexml_load_file($file);

        if (!$xml) return [];

        $ns = $xml->getNamespaces(true);
        $xml->registerXPathNamespace('nfe', $ns['']);

        $inf = $xml->xpath('//nfe:infNFe')[0] ?? null;
        if (!$inf) return [];

        $emit = $inf->emit ?? null;
        $dest = $inf->dest ?? null;
        $ide  = $inf->ide ?? null;
        $tot  = $inf->total->ICMSTot ?? null;

        $chave = str_replace('NFe', '', (string)($inf['Id'] ?? ''));

        // 🔥 NORMALIZAÇÃO CNPJ
        $cnpjEmit = preg_replace('/\D/', '', (string)($emit->CNPJ ?? ''));
        $cnpjDest = preg_replace('/\D/', '', (string)($dest->CNPJ ?? $dest->CPF ?? ''));
        $cnpjEmpresa = preg_replace('/\D/', '', (string)$cnpjEmpresa);

        // 🔥 CONTROLE GLOBAL DO PARSER (EVITA DUPLICIDADE)
        static $controle = [
            'clientes' => [],
            'fornecedores' => [],
            'itens' => [],
            'notas' => [],
            'itens_nota' => [],
            'cfop_icms' => [],
            'pagamentos' => [],
            'transporte' => [],
            'totais' => []
        ];

        // 🔥 TIPO OPERAÇÃO
        $tipo = (string)($ide->tpNF ?? '1');

        $isEntrada = false;
        $isSaida = false;

        if (!empty($cnpjEmpresa)) {
            if ($cnpjEmpresa === $cnpjDest) $isEntrada = true;
            elseif ($cnpjEmpresa === $cnpjEmit) $isSaida = true;
        }

        if (!$isEntrada && !$isSaida) {
            $isEntrada = $tipo == '0';
            $isSaida = !$isEntrada;
        }

        $dados = [
            'clientes' => [],
            'fornecedores' => [],
            'itens' => [],
            'notas' => [],
            'itens_nota' => [],
            'cfop_icms' => [],
            'pagamentos' => [],
            'transporte' => [],
            'totais' => []
        ];

        /* =========================
           FORNECEDOR (SEMPRE EMITENTE)
        ========================= */
        if ($emit && $cnpjEmit && !isset($controle['fornecedores'][$cnpjEmit])) {

            $ie = trim((string)($emit->IE ?? ''));

            $cnpj = preg_replace('/\D/', '', (string)($emit->CNPJ ?? ''));
            $cpf  = preg_replace('/\D/', '', (string)($emit->CPF ?? ''));


            $dados['fornecedores'][] = [
                'Codigo' => $cnpjEmit,
                'Nome'   => (string)$emit->xNome,
                'NomeFantasia' => (string)($emit->xFant ?? ''),
                'TipoPessoa' => 'J',
                'TipoMercado' => ($cnpj || $cpf) ? 'I' : 'E',
                'CNPJ'   => $cnpjEmit,
                'CPF'    => '',
                'IE'     => $ie,
                'IM'     => (string)($emit->IM ?? ''),
                'ContribuinteICMS' => !empty($ie) ? 'S' : 'N',
                'Fone'   => (string)($emit->enderEmit->fone ?? ''),
                'Email'  => (string)($emit->email ?? ''),
                'Endereco_fornecedores' => (string)($emit->enderEmit->xLgr ?? ''),
                'Numero_fornecedores'   => (string)($emit->enderEmit->nro ?? ''),
                'Bairro_fornecedores'   => (string)($emit->enderEmit->xBairro ?? ''),
                'CEP_fornecedores'      => (string)($emit->enderEmit->CEP ?? ''),
                'Cidade_fornecedores'   => (string)($emit->enderEmit->xMun ?? ''),
                'Estado_fornecedores'   => (string)($emit->enderEmit->UF ?? '')
            ];

            $controle['fornecedores'][$cnpjEmit] = true;
        }

        /* =========================
           CLIENTE (SEMPRE DESTINATÁRIO)
        ========================= */
        if (
            $dest &&
            $cnpjDest &&
            $cnpjDest !== $cnpjEmit && // 🔥 NÃO DUPLICA COM FORNECEDOR
            !isset($controle['clientes'][$cnpjDest])
        ) {

            $tipoPessoa = isset($dest->CNPJ) ? 'J' : 'F';

            $ie = trim((string)($dest->IE ?? ''));

            $cnpj = preg_replace('/\D/', '', (string)($dest->CNPJ ?? ''));
            $cpf  = preg_replace('/\D/', '', (string)($dest->CPF ?? ''));

            $dados['clientes'][] = [
                'Codigo' => $cnpjDest,
                'Nome'   => (string)$dest->xNome,
                'NomeFantasia' => (string)($dest->xFant ?? ''),
                'TipoPessoa' => isset($dest->CNPJ) ? 'J' : 'F',
                'TipoMercado' => ($cnpj || $cpf) ? 'I' : 'E',
                'CNPJ'   => (string)($dest->CNPJ ?? ''),
                'CPF'    => (string)($dest->CPF ?? ''),
                'IE'     => $ie,
                'IM'     => (string)($dest->IM ?? ''),
                'ContribuinteICMS' => !empty($ie) ? 'S' : 'N',
                'Fone'   => (string)($dest->enderDest->fone ?? ''),
                'Email'  => (string)($dest->email ?? ''),
                'Endereco_clientes' => (string)($dest->enderDest->xLgr ?? ''),
                'Numero_clientes'   => (string)($dest->enderDest->nro ?? ''),
                'Bairro_clientes'   => (string)($dest->enderDest->xBairro ?? ''),
                'CEP_clientes'      => (string)($dest->enderDest->CEP ?? ''),
                'Cidade_clientes'   => (string)($dest->enderDest->xMun ?? ''),
                'Estado_clientes'   => (string)($dest->enderDest->UF ?? '')
            ];

            $controle['clientes'][$cnpjDest] = true;
        }

        /* =========================
           NOTA
        ========================= */
        if (!isset($controle['notas'][$chave])) {

            $dados['notas'][] = [
                'Numero' => (string)$ide->nNF,
                'Serie' => (string)$ide->serie,
                'Modelo' => (string)$ide->mod,
                'Operacao' => (string)$ide->natOp,
                'DataEmissao' => (string)$ide->dhEmi,
                'TipoOperacao' => $tipo,
                'Participante' => $isEntrada ? (string)$emit->xNome : (string)$dest->xNome,
                'ValorTotal' => (float)($tot->vNF ?? 0),
                'ValorProdutos' => (float)($tot->vProd ?? 0),
                'ValorFrete' => (float)($tot->vFrete ?? 0),
                'ValorDesconto' => (float)($tot->vDesc ?? 0),
                'ValorICMS' => (float)($tot->vICMS ?? 0),
                'Chave' => $chave
            ];

            $controle['notas'][$chave] = true;
        }

        /* =========================
           ITENS
        ========================= */
        foreach ($inf->det as $det) {

            $prod = $det->prod;
            $imposto = $det->imposto;

            $cProd = preg_replace('/\D/', '', (string)$prod->cProd);
            $cfop  = (string)$prod->CFOP;

            // 🔥 CHAVE COMPOSTA (ANTI DUPLICIDADE REAL)
            $keyProduto = $cProd . '|' . (string)$prod->NCM . '|' . (string)$prod->uCom;
            $keyItemNota = $chave . '|' . $cProd;

            $cst = '';
            $vBC = 0;
            $vICMS = 0;

            if (isset($imposto->ICMS)) {
                foreach ($imposto->ICMS->children() as $tipoICMS) {
                    $cst = (string)($tipoICMS->CST ?? $tipoICMS->CSOSN ?? '');
                    $vBC = (float)($tipoICMS->vBC ?? 0);
                    $vICMS = (float)($tipoICMS->vICMS ?? 0);
                }
            }

            // 🔹 ITEM NOTA
            if (!isset($controle['itens_nota'][$keyItemNota])) {

                $dados['itens_nota'][] = [
                    'NumeroNF' => (string)$ide->nNF,
                    'CodigoItem' => $cProd,
                    'Quantidade' => (float)$prod->qCom,
                    'ValorItem' => (float)$prod->vProd,
                    'CFOP' => $cfop
                ];

                $controle['itens_nota'][$keyItemNota] = true;
            }

            // 🔹 PRODUTO
            if (!isset($controle['itens'][$keyProduto])) {

                $dados['itens'][] = [
                    'CodigoItem' => $cProd,
                    'Descricao' => (string)$prod->xProd,
                    'NCM' => (string)$prod->NCM,
                    'CEST' => (string)$prod->CEST,
                    'Unidade' => (string)$prod->uCom,
                    'ValorUnitario' => (float)$prod->vUnCom,
                    'EAN' => (string)$prod->cEAN
                ];

                $controle['itens'][$keyProduto] = true;
            }

            // 🔹 CFOP
            $keyCfop = $cfop . '|' . $cst;

            if (!isset($controle['cfop_icms'][$keyCfop])) {

                $dados['cfop_icms'][] = [
                    'CFOP' => $cfop,
                    'CST' => $cst,
                    'BaseICMS' => $vBC,
                    'ICMS' => $vICMS
                ];

                $controle['cfop_icms'][$keyCfop] = true;
            }
        }

        return $dados;
    }
}