# ===== CONFIGURAÇÃO =====
$DB_URL = "postgresql://schoolquest:4b5oKuGzD93ViZBKnXOL10YLm3iua2sJ@dpg-d4ida18gjchc739vgn2g-a.oregon-postgres.render.com/schoolquest"

Write-Host "Conectando ao banco..."
Write-Host ""

# ===== RESET DO BANCO =====
psql "$DB_URL" -c "DO \$\$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;"

Write-Host ""
Write-Host "Banco RESETADO com sucesso!"
