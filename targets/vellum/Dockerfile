FROM node:22-bookworm-slim
WORKDIR /srv
COPY package.json ./
RUN npm install --omit=dev --no-fund --no-audit
COPY server.js ./
COPY public ./public
EXPOSE 8087
CMD ["node", "server.js"]
