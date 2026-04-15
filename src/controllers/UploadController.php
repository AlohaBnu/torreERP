<?php

class UploadController {

    public function processar() {

        if (!isset($_FILES['arquivos'])) {
            return;
        }

        foreach ($_FILES['arquivos']['tmp_name'] as $i => $tmp) {
            $nome = $_FILES['arquivos']['name'][$i];
            Router::resolver($tmp, $nome);
        }
    }
}