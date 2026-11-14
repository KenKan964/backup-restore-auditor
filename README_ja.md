# Backup Restore Auditor

**SQLiteバックアップを独立したDBへ復元し、期待するスナップショットと内容が一致するかを検査するCLIツールです。**

**v0.1.0 · 実験版 · Python 3.11以降 · 標準ライブラリのみ · MITライセンス**

[English](README.md) | **日本語**

## 何を解決するツールか

バックアップファイルが開けたとしても、**必要な業務レコードが欠けていないか、値が変更されていないか、スキーマや外部キーが適切か**までは自動的に保証されません。

Backup Restore Auditor（BRA）は、信頼できるローカルSQLiteファイルに対して次の検査を実施する無料の開発者向けツールです。

1. バックアップをSQLiteの**読取り専用モード**で開く。
2. **SQLite Backup API**で新規ディレクトリ内の別DBへ復元する。
3. 復元したスキーマ・各表の行数・**全業務IDに対応する行ハッシュ**を、期待manifestと照合する。
4. SQLiteの整合性・外部キー検査を行い、JSON診断レポートを残す。

`capture`コマンドを使えば、元DBからバックアップと期待manifestを一緒に作成できます。ただし、**同時生成したmanifestの正当性は自動認証されません。**期待値として信頼するには、保存時の管理と独立した保管根拠が必要です。

> **対象範囲：** 管理されたローカル環境でのSQLiteスナップショット検査。実運用の災害復旧システム、最新業務状態の証明、RPO/RTO・アプリケーション継続性の保証ではありません。

## 検査できること

| 検査対象 | 検査内容 |
| --- | --- |
| DB整合性 | SQLite `PRAGMA integrity_check` |
| 外部キー | SQLite `PRAGMA foreign_key_check` |
| スキーマ | 期待スキーマのSQL文字列との厳密一致 |
| テーブルと行数 | 空表も含め、全表がmanifestに宣言されていることを確認 |
| 業務レコード | 一意でNULLでない文字列・整数IDと**全行のSHA-256** |
| 行消失・値改変 | 件数だけでは分からない行ハッシュ・キーの不一致 |
| 証拠の不足 | 不正manifest、欠落表、時点不明などを検査不能として扱う |

行数が変わらない値の改変も検出できます。ただし、manifestが過去の実際の業務状態を正しく表しているかどうかは、**本ツールだけでは確定できません。**

## クイックスタート

**必要環境：** Python 3.11以降。追加パッケージは不要です。リポジトリのルートで実行します。

```sh
python bra.py demo --out bra-demo-001
```

合成DBを生成し、バックアップと期待manifestを作成した後、別DBへ復元して照合します。主要な成果物は次のようになります。

```text
bra-demo-001/
  source.sqlite
  capture/
    backup.sqlite
    expected.json
  restore/
    restored.sqlite
    report.json
```

同梱の合成サンプルに対する検査：

```sh
python bra.py run --backup samples/backup.sqlite --manifest samples/expected.json --out bra-restore-001
```

Windowsでは必要に応じて`python`を`py -3`に置き換えてください。**毎回新しい出力ディレクトリ**が必要です。既存の出力先とsymlinkを含むパスは拒否されます。復元DBとレポートは自動削除せず、確認後に利用者が削除します。

### capture：バックアップと期待値を生成する

```sh
python bra.py capture --db samples/backup.sqlite --keys '{"people":"id","orders":"id"}' --out bra-capture-001
```

この`--keys`指定はPOSIXシェル向けです。Windows PowerShellでは、JSON引数の引用符を使用するシェルに合わせて調整してください。

`capture`は`CAPTURED_NOT_AUDITED`を返します。**独立した復元監査に合格したことを意味しません。**取得したmanifestは、期待値として利用する前に別途確認・保管してください。

## 診断結果の読み方

正常な合成デモでは、実際に記録されたJSONの次の項目が確認できます（抜粋）。

```json
{
  "schema_version": "bra-report-v1",
  "status": "MATCH",
  "exit_code": 0,
  "findings": [],
  "manifest_trust": "CALLER_SUPPLIED_NOT_EXTERNALLY_AUTHENTICATED",
  "integrity_check": ["ok"],
  "foreign_key_check": []
}
```

完全な記録は[正常デモのJSON証拠](evidence/demo.stdout.json)を参照してください。値改変・検査不能の合成例は[CLI検証記録](evidence/cli_checks.json)で確認できます。

| 終了コード | 判定 | 意味 |
| ---: | --- | --- |
| `0` | `MATCH` | **利用者が提出したmanifest**と、宣言した検査条件に一致 |
| `1` | `VIOLATION` | 検査可能な相違や整合性違反を検出 |
| `2` | `UNVERIFIABLE` | 期待値・入力・環境などの問題で信頼できる判定が不能 |

意図的な不正データを正しく検出した**テストの合格**と、不正バックアップの**CLI判定の合格**は別です。

## manifestの仕組みと信頼境界

[manifest形式の仕様](MANIFEST_FORMAT.md)と[samples/expected.json](samples/expected.json)に完全な例があります。

v1では、`method: sqlite_backup_api`、タイムゾーン付きISO 8601の`snapshot_at`、全スキーマのSQL文字列、全テーブルの`key`・`count`・`records`を指定します。行ごとに型タグを付けた値をSHA-256化し、BLOBも対象とします。キーは一意でNULLではない整数・文字列です。複合キー・曖昧照合は未対応です。

日時は`Z`、`+09:00`、`-07:00`を受け付け、タイムゾーンなしや不正な文字列は拒否します。ただし**日時の形式が正しいことは、実際の取得時刻の証明ではありません。**methodや時刻は利用者の宣言であり、暗号学的な認証は行いません。ハッシュは電子署名ではなく、推測しやすい値に関する情報漏えいリスクがあります。

## テスト・検証状況

FIX-01版は**37件の自動テスト**（元の28件＋追加9件）を含みます。独立したLinux／Python 3.13.5の審査では37件すべてに合格し、強制GC後のSQLite接続未解放`ResourceWarning`は0件でした。比較実験は4つの合成入力×2方式の8実行です。速度・ROI・汎用的な優位性は証明していません。

GitHub Actionsは**Ubuntu・Windows × Python 3.11／3.12／3.13**の6環境を対象とします。最新の実行状況は[Actions一覧](https://github.com/KenKan964/backup-restore-auditor/actions)で確認できます。`evidence/ci_status.json`の`NOT_RUN`は**登録前の履歴資料**であり、現在のCI状態を示すものではありません。

```sh
python -m unittest discover -s tests -v
python -X tracemalloc=5 tools/verify_resources.py
python compare.py > comparison-local.json
```

証拠出力を有効にする場合は`BRA_EVIDENCE`へ**新しいディレクトリ**を指定してください。既存ファイルまたはsymlinkへ書き込もうとすると、テストを失敗させます。

## 安全上の注意・制限

- **信頼できるローカルSQLiteのみ。** 悪意あるDBを安全に隔離する仕組みではありません。
- 元バックアップとcaptureの入力は読取り専用で開き、新規の独立領域にのみ復元します。任意SQLの実行・移行機能はありません。
- `.sqlite`主ファイルだけを複製すると**WALに保存された確定済み更新**が漏れる可能性があります。Backup APIでスナップショットを取得しますが、隠れたWAL欠落やDB外の業務処理を必ず検出できるわけではありません。
- `MATCH`は**最新の本番状態**や完全な災害復旧、アプリケーション継続、RPO/RTOを保証しません。
- 元DBの主ファイルSHA不変は、並行書込み時のWAL/SHM全体の不変性を保証しません。
- レポートにはテーブル名、業務IDトークン、スキーマ差分、ハッシュなどが含まれます。復元DB・manifest・レポートを機密情報として管理してください。
- 制限時間などは協調的な制限です。同一ユーザーによるファイル競合、悪意あるファイル操作、資源枯渇を完全に隔離するものではありません。

## 関連資料

[English README](README.md) · [Manifest形式](MANIFEST_FORMAT.md) · [技術仕様書](TECHNICAL_SPEC.md) · [セキュリティ](SECURITY.md) · [比較実験](OSS_COMPARISON.md) · [FIX-01変更記録](FIX01_CHANGES.md) · [是正報告書](REPORT_ja.md) · [変更履歴](CHANGELOG.md) · [MITライセンス](LICENSE)

**ライセンス：** MIT。著作権名義は[LICENSE](LICENSE)の記載に従います。一般公開前に権利関係を確認してください。
