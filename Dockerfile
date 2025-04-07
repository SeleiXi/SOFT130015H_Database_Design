FROM maven:3.8.4-openjdk-21-slim AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM openjdk:21-jre-slim
WORKDIR /app
COPY --from=build /app/target/database-import-0.0.1-SNAPSHOT.jar /app/database-import.jar
ENTRYPOINT ["java", "-jar", "/app/database-import.jar"]


