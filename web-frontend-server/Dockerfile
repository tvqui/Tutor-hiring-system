# 1. Chọn base image Node.js
FROM node:20-alpine

# 2. Thiết lập thư mục làm việc trong container
WORKDIR /usr/src/app

# 3. Copy package.json và package-lock.json
COPY package*.json ./

# 4. Cài đặt dependencies
RUN npm install

# 5. Copy toàn bộ code vào container
COPY . .

# 6. Build ứng dụng (nếu cần)
RUN npm run build

# 7. Expose port 5173
EXPOSE 5173

# 8. Chạy dev server (hoặc production serve nếu build)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
