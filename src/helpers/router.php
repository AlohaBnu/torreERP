<?php

class Router {

    public static function resolver($arquivo, $nome) {

        $conteudo = file_get_contents($arquivo);

        if (str_contains($nome, '.xml')) {
            $parser = new ParserXML();
        } elseif (str_contains($conteudo, '|C100|')) {
            $parser = new ParserSPED();
        } else {
            $parser = new ParserTXT();
        }

        $dados = $parser->parse($arquivo);

        // daqui segue para validação → ERP
    }
}