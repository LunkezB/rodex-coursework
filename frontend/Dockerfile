FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html ./
COPY tsconfig.json ./
COPY vite.config.ts ./
COPY src ./src
COPY public ./public

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
