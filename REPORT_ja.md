# BRA-DEV-001 / FIX-01 是正報告 2026-11-14

要求3点の限定是正を実装、独立再審査へ提出。既存原本とログは保持した別ディレクトリで作業。
既存28ケース＋回帰9＝37ケース、Linux Python3.13.5/3.12.14で各37/37、skip0。
ResourceWarning always設定、tracemalloc（3.13）、試験後fixture3回生成、比較8実行、GC3回でResourceWarning0。
ログtests313.log/tests312.logとresource_gate313.json/resource_gate312.jsonに環境・件数・警告0を保存。
警告ignoreやstderr破棄はせず、捕捉した警告を表示してgate失敗にする。

証拠競合は排他作成で保護。既存basic.json、file symlink先、directory symlink拒否を回帰試験。
全discoverの前後再現はbefore_conflict/after_conflict。旧版PASSでもmarker改変、修正版は非ゼロかつSHA一致。
子プロセス競合試験のstdout/stderrと前後hashを回帰JSONに保存。途中失敗を成功扱いしない。

fixture/test接続はtransaction context終了後closingで閉じる。空fixture early returnでもclose。
3回生成したファイルのrename/deleteをLinuxで確認。Windowsの実ハンドル解放確認は未実施。
日時は+09:00/-07:00/Z受理、naive/不正拒否。datetimeオブジェクトでtimezoneを確認。
時刻の真正性や業務基準時点の保証を追加したという主張はしない。

CLI MATCH/0、内容改変VIOLATION/1、時点不明UNVERIFIABLE/2を実行しcli_checks.jsonに保存。
WAL接続中、スキーマ/FK/全行hash、既存復元先拒否は元28ケースで維持。
比較8実行の期待一致は基準3/4、BRA4/4、旧契約と同じ。工数削減・ROI・需要は未測定。

Linux/Windows×3.11/3.12/3.13のCI設定にwarning gateを追加。6ジョブ全件NOT_RUN。
Windows上での再実行可能性は実ジョブでの確認が残る。ローカル結果をWindows合格へ読み替えない。
symlink試験を実施できない場合もskip合格とせずgateが失敗するため、CI実行環境の権限が必要。
公開HOLD。独立再審査とWindowsを含む6CI結果確認後に研究部が公開判断する。
任意SQL/ネットワーク/本番運用機能は追加せず、DB/manifest信頼境界・最新状態/RPO/RTO等の制約を維持。
レビュー版と軽量版に最終SHA256一覧を同梱し、全ファイルを照合。旧提出物・旧ログは事後改変しない。
