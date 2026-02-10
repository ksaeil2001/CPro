FROM node:20-alpine

WORKDIR /app

# Create non-root user for security
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser package.json package-lock.json* ./
RUN npm install

COPY --chown=appuser:appuser . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
