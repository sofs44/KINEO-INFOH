# Em app/migrations/0003_alter_preferencia_idade_parc.py

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # Isso deve corresponder ao seu arquivo de migração anterior, 
        # provavelmente '0002_...'
        ('app', '0002_alter_preferencia_idade_parc'), 
    ]

    operations = [
        # Substituímos a operação AlterField por um RunSQL manual.
        # Este SQL diz ao Postgres para:
        # 1. Mudar o TIPO da coluna para 'integer'
        # 2. Ao fazer isso, USAR o valor 'NULL' para todas as linhas existentes,
        #    em vez de tentar converter a data.
        migrations.RunSQL(
            sql='ALTER TABLE preferencias ALTER COLUMN "idade_parc" TYPE integer USING (NULL::integer);',
            
            # SQL para reverter (mudar de volta para date)
            reverse_sql='ALTER TABLE preferencias ALTER COLUMN "idade_parc" TYPE date USING (NULL::date);',
        ),
    ]