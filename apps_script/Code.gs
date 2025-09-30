/**
 * Web App de Google Apps Script para recibir ventas y escribirlas en una hoja.
 * Publicar como Web App: Implementar → Implementar implementación → Tipo: Aplicación web
 *   - Ejecutar como: Tu cuenta
 *   - Quién tiene acceso: Cualquiera con el enlace (o usuarios específicos)
 *
 * Seguridad (opcional): define la propiedad de script 'API_KEY' y envía 'X-API-Key' en el header.
 */

function doPost(e) {
  try {
    var body = e.postData && e.postData.contents ? e.postData.contents : null;
    if (!body) return _json({ success: false, error: 'EMPTY_BODY' }, 400);

    var data = JSON.parse(body);
    var action = data.action || '';

    // Validar API_KEY si está configurada
    var props = PropertiesService.getScriptProperties();
    var requiredKey = props.getProperty('API_KEY');
    if (requiredKey) {
      var headers = e.headers || {};
      var sentKey = headers['X-API-Key'] || headers['x-api-key'] || '';
      if (sentKey !== requiredKey) {
        return _json({ success: false, error: 'UNAUTHORIZED' }, 401);
      }
    }

    if (action === 'status') {
      var ss = _openSpreadsheet_();
      var ws = _getWorksheet_(ss);
      return _json({ success: true, title: ss.getName(), sheet: ws.getName(), lastRow: ws.getLastRow() });
    }

    if (action === 'appendRows') {
      var rows = data.rows || [];
      if (!rows.length) return _json({ success: false, error: 'NO_ROWS' }, 400);

      var ss = _openSpreadsheet_();
      var ws = _getWorksheet_(ss);

    // Calcular siguiente fila después de la última con datos (simple y efectivo)
    var startRow = _getFirstEmptyRow_(ws); // deja fila 1 para headers
      var numRows = rows.length;
      var numCols = rows[0].length;
      var range = ws.getRange(startRow, 1, numRows, numCols);
      range.setValues(rows);

      return _json({ success: true, appended: numRows, startRow: startRow });
    }

    return _json({ success: false, error: 'UNKNOWN_ACTION' }, 400);
  } catch (err) {
    return _json({ success: false, error: String(err) }, 500);
  }
}

function _openSpreadsheet_() {
  // Configurar por ID o URL en Propiedades del Script: SHEET_ID y SHEET_NAME
  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty('SHEET_ID');
  if (!sheetId) throw new Error('SHEET_ID no configurado en propiedades del script');
  return SpreadsheetApp.openById(sheetId);
}

function _getWorksheet_(ss) {
  var props = PropertiesService.getScriptProperties();
  var sheetName = props.getProperty('SHEET_NAME') || 'Ingreso Diario';
  var ws = ss.getSheetByName(sheetName);
  if (!ws) ws = ss.insertSheet(sheetName);
  return ws;
}

function _json(obj, code) {
  var output = ContentService.createTextOutput(JSON.stringify(obj));
  output.setMimeType(ContentService.MimeType.JSON);
  if (code) output.setContent(JSON.stringify(Object.assign({ code: code }, obj)));
  return output;
}

// Retorna la siguiente fila después de la última con contenido
function _getFirstEmptyRow_(ws) {
  var lastRow = ws.getLastRow();
  return lastRow < 2 ? 2 : lastRow + 1;
}

// Encuentra la siguiente fila realmente vacía (ignora filas con solo formato/espacios)
function getNextSmartRow_(ws) {
  var lastRow = ws.getLastRow();
  if (lastRow < 2) return 2; // reserva fila 1 para headers

  // Lee un bloque razonable hacia arriba para detectar la última fila con datos significativos
  var start = Math.max(2, lastRow - 999); // hasta 1000 filas hacia arriba
  var numRows = lastRow - start + 1;
  var values = ws.getRange(start, 1, numRows, ws.getLastColumn()).getValues();

  for (var i = values.length - 1; i >= 0; i--) {
    var row = values[i];
    if (_rowHasMeaningfulData_(row)) {
      return start + i + 1; // siguiente fila después de la última con datos reales
    }
  }
  return 2;
}

function _rowHasMeaningfulData_(row) {
  for (var j = 0; j < row.length; j++) {
    var cell = row[j];
    if (cell === null || cell === undefined) continue;
    var s = String(cell).trim();
    if (s && ['-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none', '$0,00', '$0.00', '0', '0.00', '0,00'].indexOf(s) === -1) {
      return true;
    }
  }
  return false;
}

// Soporte GET para ver estado desde el navegador (opcional)
function doGet(e) {
  try {
    // Validar API_KEY en GET si existe (por query param apiKey)
    var props = PropertiesService.getScriptProperties();
    var cfgKey = (typeof CONFIG !== 'undefined' && CONFIG.API_KEY) ? CONFIG.API_KEY : '';
    var requiredKey = props.getProperty('API_KEY') || cfgKey || '';
    if (requiredKey) {
      var params = (e && e.parameter) ? e.parameter : {};
      var sentKey = params['apiKey'] || params['apikey'] || '';
      if (sentKey !== requiredKey) {
        return _json({ success: false, error: 'UNAUTHORIZED' }, 401);
      }
    }

    var ss = _openSpreadsheet_();
    var ws = _getWorksheet_(ss);
    return _json({
      success: true,
      method: 'GET',
      hint: 'Usa POST con action=appendRows para escribir filas',
      title: ss.getName(),
      sheet: ws.getName(),
      lastRow: ws.getLastRow()
    });
  } catch (err) {
    return _json({ success: false, error: String(err) }, 500);
  }
}


