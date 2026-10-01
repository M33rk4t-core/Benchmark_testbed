FROM node:22-bookworm-slim
WORKDIR /srv
COPY package.json ./
RUN npm install --omit=dev --no-fund --no-audit
COPY server.js ./
COPY drawings ./drawings
EXPOSE 8091
CMD ["node", "server.js"]
