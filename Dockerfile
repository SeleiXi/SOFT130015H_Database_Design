FROM maven:3.8.4-openjdk-11-slim AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=build /app/target/database-import-0.0.1-SNAPSHOT.jar /app/database-import.jar
ENTRYPOINT ["java", "-jar", "/app/database-import.jar"]


