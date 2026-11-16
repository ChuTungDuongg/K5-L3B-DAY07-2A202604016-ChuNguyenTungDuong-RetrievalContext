# Nguồn và điều kiện sử dụng dữ liệu

Các chunk văn bản và vector trong bài này được tạo từ **Introduction to Computer Science**, OpenStax, Rice University, ©2026 Rice University. Access for free at openstax.org.

- Nguồn: https://openstax.org/details/books/introduction-computer-science
- PDF: https://assets.openstax.org/oscms-prodcms/media/documents/Introduction_To_Computer_Science_-_WEB.pdf
- Giấy phép ghi tại trang PDF vật lý 4: Creative Commons Attribution Non-Commercial ShareAlike 4.0 International, https://creativecommons.org/licenses/by-nc-sa/4.0/.
- Phạm vi dùng: 38 trang vật lý 370 đến 410, loại 389, 394, 408. Manifest gốc được giữ trong `day6_manifest.json`.
- Thay đổi: trích xuất và chuẩn hóa văn bản ở Day 6, chia cửa sổ 500 ký tự với overlap 50, tạo 273 vector 384 chiều. Day 7 dùng lại snapshot đó. Nội dung có thể bị cắt giữa câu và còn đầu/chân trang.
- Các trích đoạn được chia sẻ cho bài thực hành giáo dục phi thương mại với ghi công và điều kiện chia sẻ tương tự của nguồn. Không gán giấy phép phần mềm cho văn bản sách. Các hình và tên thương mại trong sách có thể có ghi công hoặc quyền riêng.

Thông tin này áp dụng cho cả JSON chunk, snapshot vector và trích đoạn nằm trong trace kết quả. Không đưa tài liệu mật hoặc dữ liệu của tài khoản cá nhân vào corpus.

## Nguồn riêng cho phần nâng cao

World Bank. 2021. *World Development Report 2021: Data for Better Lives*. Washington, DC: World Bank. doi:10.1596/978-1-4648-1600-0. License: CC BY 3.0 IGO. [PDF nguồn](https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf), 350 trang vật lý, SHA-256 `606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616`.

Thay đổi phục vụ thực hành gồm trích native text, chia chunk, mô tả vùng trực quan bằng model, tạo vector và dẫn chứng trong trace. Đây là bản xử lý từ tài liệu gốc, không được World Bank bảo chứng. Không áp giấy phép phần mềm của repo cho tài liệu nguồn. Trang PDF 4 nêu điều kiện ghi công, bản thích nghi và quyền đối với thành phần bên thứ ba. Repo không đóng gói PDF gốc hoặc toàn bộ ảnh trang, mà cung cấp cách tải, checksum và render để kiểm chứng hợp lệ. Các hình mẫu được trích để kiểm chứng vùng evidence và giữ nguồn ghi công.
