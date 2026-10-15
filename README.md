# MiniWatts — Bản Việt hóa

Repo này tự động lấy source mới nhất từ [`ResistanceTo/MiniWatts`](https://github.com/ResistanceTo/MiniWatts), thêm locale tiếng Việt cho toàn bộ `Localizable.xcstrings` của app và Widget, kiểm tra không còn chuỗi có thể dịch nào bị thiếu locale `vi`, sau đó build IPA unsigned.

## Lấy file đã build

Vào **Actions → Build MiniWatts Vietnamese → run mới nhất → Artifacts**.

Có 2 artifact:

- `MiniWatts-Vietnamese-source`: source MiniWatts đã thêm tiếng Việt, có thể mở bằng Xcode và tự build.
- `MiniWatts-Vietnamese-unsigned-ipa`: IPA unsigned để bạn tự ký bằng chứng chỉ/Apple ID của mình.

## Build lại

Mỗi lần push lên nhánh `main`, workflow tự chạy. Bạn cũng có thể vào **Actions → Build MiniWatts Vietnamese → Run workflow** để build thủ công.

## Nguyên tắc Việt hóa

- Giữ nguyên tên API, sensor key, USB-C, đơn vị kỹ thuật và placeholder như `%@`, `%lld`, `${metric}`.
- Dịch toàn bộ mục có thể dịch trong String Catalog sang `vi`.
- Các thuật ngữ sạc/pin quan trọng được chuẩn hóa thủ công; các câu mô tả dài được dịch tự động từ tiếng Anh rồi ghi trực tiếp vào String Catalog trước khi build.
- Không sửa logic đo công suất, cảm biến hay lịch sử sạc của MiniWatts.

> Đây là bản Việt hóa không chính thức. MiniWatts gốc thuộc tác giả upstream và tiếp tục tuân theo giấy phép của dự án gốc.
