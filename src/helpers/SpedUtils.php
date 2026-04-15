<?php

class SpedUtils {

    public static function toFloat($valor): float {
        if ($valor === '' || $valor === null) {
            return 0.0;
        }
        return (float) str_replace(',', '.', $valor);
    }
}
