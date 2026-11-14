# FIX-01差分と再現

bra.py: fixture接続をclosingで囲み、既存transaction contextの後にclose。日時の文字列プラス記号判定をtzinfo/utcoffset判定へ置換。
tests/test_acceptance.py: 生接続のcontextをclosingで囲みcommit/rollbackを維持。既存WAL接続のfinally.closeは保持。
BRA_EVIDENCEは排他open x。既存ファイルとsymlink経路で例外を返しテスト失敗にする。
tests/test_fix01.py: 既存ファイル競合、file/directory symlink、fixture3回のrename/delete、日時5種類を追加。
tools/verify_resources.py: 全試験後fixture3回・比較実行・GC3回、ResourceWarning0を判定し警告も表示。
比較の業務ロジック・28ケースの期待判定は未変更。正確なdiffはFIX01.patch。

新規先で BRA_EVIDENCE=fresh python3.13 -W always::ResourceWarning -X tracemalloc=5 tools/verify_resources.py
競合: 一時evidence/basic.jsonに合成markerを置きBRA_EVIDENCEへ指定して全discoverを実行。
旧版28件PASS/marker変更→修正版37件実行/非ゼロ終了/markerSHA不変を記録。
回帰単独: python3.13 -m unittest discover -s tests -p test_fix01.py -v
時間テスト・hash記録・子stdout/stderrはevidence/acceptance313以下。旧提出物・旧ログは改変しない。
