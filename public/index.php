<?php

function formatarDataSped(?string $data): string
{
    if (!$data || strlen($data) !== 8) {
        return '';
    }

    return substr($data, 0, 2) . '/'
         . substr($data, 2, 2) . '/'
         . substr($data, 4, 4);
}

session_start();
require_once __DIR__ . '/../src/parsers/ParserSPED.php';
require_once __DIR__ . '/../src/parsers/ParserXML.php';


/* EXPORTAÇÃO CSV */
if (isset($_GET['export']) && isset($_SESSION['sped'])) {

    $tipo = $_GET['export'];
    $dados = $_SESSION['sped'][$tipo] ?? [];

    header('Content-Type: text/csv; charset=UTF-8');
    header("Content-Disposition: attachment; filename={$tipo}.csv");

    $out = fopen('php://output', 'w');
    fprintf($out, chr(0xEF).chr(0xBB).chr(0xBF));

    if (!empty($dados)) {

    // ✅ CASO 1: array de registros (ex: clientes, fornecedores, itens, notas)
    if (isset($dados[0]) && is_array($dados[0])) {

        fputcsv($out, array_keys($dados[0]), ';');

        foreach ($dados as $row) {

            // 🔒 garante que nenhum valor seja array
            foreach ($row as $chave => $valor) {
                if (is_array($valor)) {
                    $row[$chave] = json_encode($valor, JSON_UNESCAPED_UNICODE);
                }
            }

            fputcsv($out, $row, ';');
        }

    }
    // ✅ CASO 2: array associativo simples (ex: apuração ICMS)
    else {

        fputcsv($out, ['Campo', 'Valor'], ';');

        foreach ($dados as $campo => $valor) {

            if (is_array($valor)) {
                $valor = json_encode($valor, JSON_UNESCAPED_UNICODE);
            }

            fputcsv($out, [$campo, $valor], ';');
        }
    }
}


    fclose($out);
    exit;
}

/* IMPORTAÇÃO SPED */
if (
    $_SERVER['REQUEST_METHOD'] === 'POST' &&
    isset($_FILES['arquivo']) &&
    isset($_FILES['arquivo']['tmp_name']) &&
    $_FILES['arquivo']['error'] === UPLOAD_ERR_OK &&
    !empty($_FILES['arquivo']['tmp_name'])
) {

    // 🔥 LIMPA XML
    unset($_SESSION['xml']);
    unset($_SESSION['xml_chaves']);

    $parser = new ParserSPED();
    $_SESSION['sped'] = $parser->parse($_FILES['arquivo']['tmp_name']);

    // 🔥 DEFINE MODO
    $_SESSION['modo'] = 'sped';

    header("Location: " . $_SERVER['PHP_SELF']);
    exit;
}

/* IMPORTAÇÃO XML */
if (
    $_SERVER['REQUEST_METHOD'] === 'POST' &&
    isset($_FILES['xmls']) &&
    isset($_FILES['xmls']['tmp_name'][0]) &&
    $_FILES['xmls']['error'][0] === UPLOAD_ERR_OK
) {

    // 🔥 LIMPA SPED
    unset($_SESSION['sped']);

    $_SESSION['xml'] = [];
    $_SESSION['xml_chaves'] = [];

    $parserXml = new ParserXML();

    foreach ($_FILES['xmls']['tmp_name'] as $i => $tmp) {

        if ($_FILES['xmls']['error'][$i] !== UPLOAD_ERR_OK) continue;

        $cnpjEmpresa = $_SESSION['sped']['empresa']['CNPJ'] ?? null;

        $dados = $parserXml->parse($tmp, $cnpjEmpresa);

        if (empty($dados)) continue;

        $chave = $dados['notas'][0]['Chave'] ?? null;

        if ($chave && in_array($chave, $_SESSION['xml_chaves'])) continue;

        $_SESSION['xml_chaves'][] = $chave;
        $_SESSION['xml'][] = $dados;
    }

    // 🔥 DEFINE MODO
    $_SESSION['modo'] = 'xml';

    header("Location: " . $_SERVER['PHP_SELF']);
    exit;
}

$d = $_SESSION['sped'] ?? [];
$xmls = $_SESSION['xml'] ?? [];

$modo = $_SESSION['modo'] ?? null;

$d = [];
$xmls = $_SESSION['xml'] ?? [];

if ($modo === 'sped') {
    $d = $_SESSION['sped'] ?? [];
}

if ($modo === 'xml') {
    // 🔥 AQUI ESTÁ O PULO DO GATO
    // transforma XML no mesmo formato visual do SPED

    $d = [
        'clientes' => [],
        'fornecedores' => [],
        'itens' => [],
        'notas' => [],
        'itens_nota' => [],
        'cfop_icms' => []
    ];

    foreach ($xmls as $xml) {

        foreach ($xml as $tipo => $lista) {

            if (!isset($d[$tipo])) {
                $d[$tipo] = [];
            }

            if (is_array($lista)) {
                $d[$tipo] = array_merge($d[$tipo], $lista);
            }
        }
    }
}
?>


<!DOCTYPE html>
<html lang="pt-BR">
<head>
<style>
.table thead th {
    position: sticky;
    top: 0;
    background: white;
    z-index: 2;
}

.table td:first-child,
.table th:first-child {
    position: sticky;
    left: 0;
    background: white;
    z-index: 1;
}
</style>
<meta charset="UTF-8">
<title>Migrador SPED</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-light">
<div class="container mt-4">

<h4>Migrador SPED Fiscal</h4>

<form method="post" enctype="multipart/form-data" class="mb-4">
    <input type="file" name="arquivo" required>
    <button class="btn btn-primary btn-sm">Importar SPED</button>
</form>

<form method="post" enctype="multipart/form-data" class="mb-4">
    <label><strong>Importar XML (NF-e)</strong></label><br>
    <input type="file" name="xmls[]" multiple accept=".xml">
    <button class="btn btn-warning btn-sm">Importar XML</button>
</form>

<?php if ($_SESSION['modo'] === 'xml' && !empty($xmls)): ?>

    <?php if (!empty($d['empresa'])): ?>

        <!-- SEU CARD EMPRESA AQUI -->

    <?php endif; ?>

    <!-- RESTANTE DAS ABAS AQUI -->

<?php endif; ?>

<!-- EMPRESA -->
<div class="card mb-4">
  <div class="card-header fw-bold">Empresa (Registro 0000)</div>
  <div class="card-body">
    <div class="row">
      <div class="col"><strong>Razão Social:</strong> <?= $d['empresa']['RazaoSocial'] ?? '—' ?></div>
      <div class="col"><strong>CNPJ:</strong> <?= $d['empresa']['CNPJ'] ?? '—' ?></div>
      <div class="col"><strong>IE:</strong> <?= $d['empresa']['IE'] ?? '—' ?></div>
      <div class="col"><strong>UF:</strong> <?= $d['empresa']['UF'] ?? '—' ?></div>
      <div class="col"><strong>Período:</strong> <?= formatarDataSped($d['empresa']['DataInicial'] ?? '') ?> a <?= formatarDataSped($d['empresa']['DataFinal'] ?? '') ?></div>
    </div>
  </div>
</div>

<?php
$abas = [
  'clientes' => 'Clientes (Saída)',
  'fornecedores' => 'Fornecedores (Entrada)',
  'itens' => 'Produtos (0200)',
  'notas' => 'Notas Fiscais (C100)',
  'itens_nota' => 'Itens da Nota (C170)',
  'cfop_icms' => 'CFOP / ICMS (C190)',
  'apuracao' => 'Apuração ICMS (E110)',
  'xml' => 'XML (NF-e)'

];
?>

<ul class="nav nav-tabs">
<?php foreach ($abas as $k => $v): ?>
  <li class="nav-item">
    <a class="nav-link <?= $k === 'clientes' ? 'active' : '' ?>" data-bs-toggle="tab" href="#<?= $k ?>"><?= $v ?></a>
  </li>
<?php endforeach; ?>
</ul>

<div class="tab-content bg-white border p-3">

<!-- CLIENTES -->
<div class="tab-pane fade show active" id="clientes">
    <a class="btn btn-success btn-sm mb-2" href="?export=clientes">Exportar CSV</a>
    <a href="?enviar=clientes" class="btn btn-primary btn-sm mb-2">Enviar Clientes para ERP</a>

    <div class="table-responsive">
        <table class="table table-sm table-striped table-nowrap">
            <tr>
                <th>Código</th><th>Nome</th><th>Fantasia</th><th>Tipo</th><th>Mercado</th>
                <th>CNPJ</th><th>CPF</th><th>IE</th><th>IM</th><th>ICMS</th>
                <th>Fone</th><th>Email</th><th>Endereço</th><th>Nº</th>
                <th>CEP</th><th>Bairro</th><th>Cidade</th><th>Estado</th>
            </tr>

            <?php foreach (($d['clientes'] ?? []) as $c): ?>
            <tr>
                <td><?= $c['Codigo'] ?? '' ?></td>
                <td><?= htmlspecialchars($c['Nome'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['NomeFantasia'] ?? '') ?></td>
                <td><?= $c['TipoPessoa'] ?? '' ?></td>
                <td><?= $c['TipoMercado'] ?? '' ?></td>
                <td><?= $c['CNPJ'] ?? '' ?></td>
                <td><?= $c['CPF'] ?? '' ?></td>
                <td><?= $c['IE'] ?? '' ?></td>
                <td><?= htmlspecialchars($c['IM'] ?? '') ?></td>
                <td><?= $c['ContribuinteICMS'] ?? '' ?></td>
                <td><?= htmlspecialchars($c['Fone'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Email'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Endereco_clientes'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Numero_clientes'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['CEP_clientes'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Bairro_clientes'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Cidade_clientes'] ?? '') ?></td>
                <td><?= htmlspecialchars($c['Estado_clientes'] ?? '') ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </div>
</div> <!-- ✅ FECHAMENTO CORRETO -->



<!-- FORNECEDORES -->
<div class="tab-pane fade" id="fornecedores">
    <a class="btn btn-success btn-sm mb-2" href="?export=fornecedores">Exportar CSV</a>
    <a href="?enviar=fornecedores" class="btn btn-primary btn-sm mb-2">Enviar Fornecedores para ERP</a>

    <div class="table-responsive">
        <table class="table table-sm table-striped table-nowrap">
            <tr>
                <th>Código</th><th>Nome</th><th>Fantasia</th><th>Tipo</th><th>Mercado</th>
                <th>CNPJ</th><th>CPF</th><th>IE</th><th>IM</th><th>ICMS</th>
                <th>Fone</th><th>Email</th><th>Endereço</th><th>Nº</th>
                <th>CEP</th><th>Bairro</th><th>Cidade</th><th>Estado</th>
            </tr>

            <?php foreach (($d['fornecedores'] ?? []) as $f): ?>
            <tr>
                <td><?= $f['Codigo'] ?? '' ?></td>
                <td><?= htmlspecialchars($f['Nome'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['NomeFantasia'] ?? '') ?></td>
                <td><?= $f['TipoPessoa'] ?? '' ?></td>
                <td><?= $f['TipoMercado'] ?? '' ?></td>
                <td><?= $f['CNPJ'] ?? '' ?></td>
                <td><?= $f['CPF'] ?? '' ?></td>
                <td><?= $f['IE'] ?? '' ?></td>
                <td><?= htmlspecialchars($f['IM'] ?? '') ?></td>
                <td><?= $f['ContribuinteICMS'] ?? '' ?></td>
                <td><?= htmlspecialchars($f['Fone'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Email'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Endereco_fornecedores'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Numero_fornecedores'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['CEP_fornecedores'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Bairro_fornecedores'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Cidade_fornecedores'] ?? '') ?></td>
                <td><?= htmlspecialchars($f['Estado_fornecedores'] ?? '') ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </div>
</div>

<!-- ITENS -->
<div class="tab-pane fade" id="itens">
<a class="btn btn-success btn-sm mb-2" href="?export=itens">Exportar CSV</a>
<a href="?enviar=itens" class="btn btn-primary btn-sm mb-2">Enviar Produtos para ERP</a>
<div class="table-responsive">
<table class="table table-sm table-striped table-nowrap">
<tr><th>Código</th><th>Descrição</th><th>NCM</th><th>Unidade</th></tr>
<?php foreach (($d['itens'] ?? []) as $i): ?>
<tr>
<td><?= $i['CodigoItem'] ?? '' ?></td>
<td><?= htmlspecialchars($i['Descricao'] ?? '') ?></td>
<td><?= $i['NCM'] ?? '' ?></td>
<td><?= $i['Unidade'] ?? '' ?></td>
</tr>
<?php endforeach; ?>
</table>
</div>

<!-- NOTAS -->
<div class="tab-pane fade" id="notas">
<a class="btn btn-success btn-sm mb-2" href="?export=notas">Exportar CSV</a>
<a href="?enviar=notas" class="btn btn-primary btn-sm mb-2">Enviar Notas para ERP</a>
<div class="table-responsive">
<table class="table table-sm table-striped table-nowrap">
<tr><th>Número</th><th>Operação</th><th>Participante</th><th>Valor Total</th></tr>
<?php foreach (($d['notas'] ?? []) as $n): ?>
<tr>
<td><?= $n['Numero'] ?? '' ?></td>
<td><?= $n['Operacao'] ?? '' ?></td>
<td><?= $n['Participante'] ?? '' ?></td>
<td><?= number_format($n['ValorTotal'],2,',','.') ?? '0,00' ?></td>
</tr>
<?php endforeach; ?>
</table>
</div>

<!-- ITENS DA NOTA -->
<div class="tab-pane fade" id="itens_nota">
<a class="btn btn-success btn-sm mb-2" href="?export=itens_nota">Exportar CSV</a>
<a href="?enviar=itens_nota" class="btn btn-primary btn-sm mb-2">Enviar Itens da Nota para ERP</a>
<div class="table-responsive">
<table class="table table-sm table-striped table-nowrap">
<tr><th>Nº NF</th><th>Código Item</th><th>Quantidade</th><th>Valor</th><th>CFOP</th></tr>
<?php foreach (($d['itens_nota'] ?? []) as $f): ?>
<tr>
<td><?= $f['NumeroNF'] ?? '' ?></td>
<td><?= $f['CodigoItem'] ?? '' ?></td>
<td><?= $f['Quantidade'] ?? '' ?></td>
<td><?= number_format($f['ValorItem'],2,',','.') ?? '0,00' ?></td>
<td><?= $f['CFOP'] ?? '' ?></td>
</tr>
<?php endforeach; ?>
</table>
</div>

<!-- CFOP -->
<div class="tab-pane fade" id="cfop_icms">
<a class="btn btn-success btn-sm mb-2" href="?export=cfop_icms">Exportar CSV</a>
<a href="?enviar=cfop_icms" class="btn btn-primary btn-sm mb-2">Enviar CFOP para ERP</a>
<div class="table-responsive">
<table class="table table-sm table-striped table-nowrap">
<tr><th>CFOP</th><th>Base ICMS</th><th>ICMS</th></tr>
<?php foreach (($d['cfop_icms'] ?? []) as $c): ?>
<tr>
<td><?= $c['CFOP'] ?? '' ?></td>
<td><?= number_format($c['BaseICMS'],2,',','.') ?? '0,00' ?></td>
<td><?= number_format($c['ICMS'],2,',','.') ?? '0,00'  ?></td>
</tr>
<?php endforeach; ?>
</table>
</div>

<!-- APURAÇÃO -->
<div class="tab-pane fade" id="apuracao">
<a class="btn btn-success btn-sm mb-2" href="?export=apuracao">Exportar CSV</a>]
<a href="?enviar=apuracao" class="btn btn-primary btn-sm mb-2">Enviar Apuração para ERP</a>
<table class="table table-sm">
<tr><th>ICMS a Recolher</th><th>Saldo Credor</th></tr>
<tr>
<?php
$apuracao = $d['apuracao'] ?? [
    'ICMSRecolher' => 0,
    'SaldoCredor' => 0
];
?>

<td><?= number_format($apuracao['ICMSRecolher'], 2, ',', '.') ?></td>
<td><?= number_format($apuracao['SaldoCredor'], 2, ',', '.') ?></td>
</tr>
</table>
</div>

</div>

<!-- XML -->
<div class="tab-pane fade" id="xml">

<?php if (!empty($xmls)): ?>

<?php foreach ($xmls as $xml): 
    $nota = $xml['notas'][0] ?? null;
    $total = $xml['totais'][0] ?? null;
?>

<div class="card mb-4 shadow">

  <div class="card-header bg-dark text-white">
    <strong>NF-e Nº <?= $nota['Numero'] ?></strong>
    | <?= $nota['Participante'] ?>
  </div>

  <div class="card-body">

    <!-- RESUMO -->
    <div class="row mb-3">
        <div class="col"><strong>Tipo:</strong> <?= $nota['TipoOperacao'] == '0' ? 'Entrada' : 'Saída' ?></div>
        <div class="col"><strong>Valor Total:</strong> R$ <?= number_format($nota['ValorTotal'],2,',','.') ?></div>
        <div class="col"><strong>Chave:</strong> <?= $nota['Chave'] ?></div>
    </div>

    <!-- TOTAIS -->
    <div class="mb-3">
        <h6>Totais Fiscais</h6>
        <div class="row">
            <div class="col">Produtos: <?= number_format($total['vProd'],2,',','.') ?></div>
            <div class="col">ICMS: <?= number_format($total['vICMS'],2,',','.') ?></div>
            <div class="col">IPI: <?= number_format($total['vIPI'],2,',','.') ?></div>
            <div class="col">PIS: <?= number_format($total['vPIS'],2,',','.') ?></div>
            <div class="col">COFINS: <?= number_format($total['vCOFINS'],2,',','.') ?></div>
        </div>
    </div>

    <!-- ITENS -->
    <h6>Itens</h6>
    <table class="table table-sm table-bordered">
      <thead class="table-light">
        <tr>
          <th>Código</th>
          <th>Descrição</th>
          <th>Qtd</th>
          <th>Valor</th>
          <th>CFOP</th>
          <th>CST</th>
          <th>ICMS</th>
        </tr>
      </thead>
      <tbody>

      <?php foreach ($xml['itens_nota'] as $i => $item): 
            $produto = $xml['itens'][$i] ?? [];
            $imposto = $xml['cfop_icms'][$i] ?? [];
      ?>
        <tr>
          <td><?= $item['CodigoItem'] ?></td>
          <td><?= $produto['Descricao'] ?? '' ?></td>
          <td><?= $item['Quantidade'] ?></td>
          <td><?= number_format($item['ValorItem'],2,',','.') ?></td>
          <td><?= $item['CFOP'] ?></td>
          <td><?= $imposto['CST'] ?? '' ?></td>
          <td><?= number_format($imposto['ICMS'] ?? 0,2,',','.') ?></td>
        </tr>
      <?php endforeach; ?>

      </tbody>
    </table>

    <!-- PAGAMENTO -->
    <?php if (!empty($xml['pagamentos'])): ?>
    <h6>Pagamentos</h6>
    <table class="table table-sm">
        <tr><th>Tipo</th><th>Valor</th></tr>
        <?php foreach ($xml['pagamentos'] as $p): ?>
        <tr>
            <td><?= $p['Tipo'] ?></td>
            <td><?= number_format($p['Valor'],2,',','.') ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    <?php endif; ?>

    <!-- TRANSPORTE -->
    <?php if (!empty($xml['transporte'])): ?>
    <h6>Transporte</h6>
    <?php foreach ($xml['transporte'] as $t): ?>
        <div class="row mb-2">
            <div class="col">Modalidade: <?= $t['ModalidadeFrete'] ?></div>
            <div class="col">Transportadora: <?= $t['Transportadora'] ?></div>
            <div class="col">CNPJ: <?= $t['CNPJ'] ?></div>
            <div class="col">UF: <?= $t['UF'] ?></div>
        </div>
    <?php endforeach; ?>
    <?php endif; ?>

  </div>
</div>

<?php endforeach; ?>

<?php else: ?>
<div class="alert alert-info">
    Nenhum XML carregado.
</div>
<?php endif; ?>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

<script>
document.addEventListener("DOMContentLoaded", function () {

    // 🔥 CONTROLE DAS ABAS
    const aba = localStorage.getItem("abaAtiva");

    if (aba) {
        const trigger = document.querySelector(`[href="${aba}"]`);
        if (trigger) new bootstrap.Tab(trigger).show();
    }

    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function () {
            localStorage.setItem("abaAtiva", this.getAttribute("href"));
        });
    });

    // 🔥 ABERTURA DO MODAL
    document.querySelectorAll('a[href^="?enviar="]').forEach(function (link) {

        link.addEventListener('click', function (event) {

            event.preventDefault();

            const href = this.getAttribute('href');
            const params = new URLSearchParams(href.replace('?', ''));
            const entidade = params.get('enviar');

            document.getElementById('entidadeSelecionada').value = entidade;

            const modal = new bootstrap.Modal(
                document.getElementById('modalWebService')
            );
            modal.show();

        });

    });

});
</script>

<!-- MODAL WEBSERVICE ERP -->
<div class="modal fade" id="modalWebService" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">

      <form method="post">

        <div class="modal-header">
          <h5 class="modal-title">Enviar dados para o ERP</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>

        <div class="modal-body">

          <input type="hidden" name="entidade" id="entidadeSelecionada">

          <div class="mb-3">
            <label class="form-label">URL do WebService</label>
            <input type="text" name="url_ws" class="form-control"
                   placeholder="https://erp.exemplo.com/api/importar"
                   required>
          </div>

          <div class="mb-3">
            <label class="form-label">Token / API Key</label>
            <input type="text" name="token" class="form-control" required>
          </div>

          <div class="row mb-3">
            <div class="col">
              <label class="form-label">Usuário</label>
              <input type="text" name="usuario" class="form-control">
            </div>
            <div class="col">
              <label class="form-label">Senha</label>
              <input type="password" name="senha" class="form-control">
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">Ambiente</label>
            <select class="form-select" name="ambiente">
              <option value="homologacao">Homologação</option>
              <option value="producao">Produção</option>
            </select>
          </div>

        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            Cancelar
          </button>
          <button type="submit" name="confirmar_envio" class="btn btn-success">
            Confirmar Envio
          </button>
        </div>

      </form>

    </div>
  </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function () {

    const aba = localStorage.getItem("abaAtiva");

    if (aba) {
        const trigger = document.querySelector(`[href="${aba}"]`);
        if (trigger) new bootstrap.Tab(trigger).show();
    }

    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function () {
            localStorage.setItem("abaAtiva", this.getAttribute("href"));
        });
    });

});
</script>

</body>
</html>