FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

ENV VITE_BACKEND_URL=http://nexus-backend:8000

# Run as an unprivileged user (node image ships the `node` user)
RUN chown -R node:node /app
USER node

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
